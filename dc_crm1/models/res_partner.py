# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import requests
import json
from odoo.addons.base.models.ir_ui_view import keep_query
from datetime import datetime, timedelta, MINYEAR, date
import logging
_logger = logging.getLogger(__name__)

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.osv.expression import get_unaccent_wrapper
from odoo.addons.base.models import res_partner
from odoo.tools import remove_accents
import logging


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    facebook = fields.Char()
    Linkedin = fields.Char()
    is_control = fields.Boolean() 
    hobby = fields.Char('Sở thích')
    # birthdate = fields.Date()
    

    # def name_get(self):
    #     res = []
    #     for r in self:
    #         res.append((r.id, '{}{}'.format(employee.name, employee.job_title and (' - ' + employee.job_title) or '')))
    #     return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        if name and operator in ('=', 'ilike', '=ilike', 'like', '=like'):
            self.check_access_rights('read')
            where_query = self._where_calc(args)
            self._apply_ir_rules(where_query, 'read')
            from_clause, where_clause, where_clause_params = where_query.get_sql()
            where_str = where_clause and (" WHERE %s AND " % where_clause) or ' WHERE '

            # search on the name of the contacts and of its company
            search_name = name
            if operator in ('ilike', 'like'):
                search_name = '%%%s%%' % name
            if operator in ('=ilike', '=like'):
                operator = operator[1:]

            unaccent = get_unaccent_wrapper(self.env.cr)

            query = """SELECT id
                         FROM res_partner
                      {where} ({email} {operator} {percent}
                           OR {display_name} {operator} {percent}
                           OR {reference} {operator} {percent}
                           OR {phone} {operator} {percent}
                           OR {mobile} {operator} {percent}
                           OR {mobile2} {operator} {percent}
                           OR {mobile3} {operator} {percent}
                           OR {address2} {operator} {percent}
                           OR {name_unaccent} {operator} {percent})
                           -- don't panic, trust postgres bitmap
                     ORDER BY {display_name} {operator} {percent} desc,
                              {display_name}
                    """.format(where=where_str,
                               operator=operator,
                               email=unaccent('email'),
                               display_name=unaccent('display_name'),
                               reference=unaccent('ref'),
                               phone=unaccent('phone'),
                               mobile=unaccent('mobile'),
                               mobile2=unaccent('mobile2'),
                               mobile3=unaccent('mobile3'),
                               address2=unaccent('address2'),
                               name_unaccent=unaccent('name_unaccent'),
                               percent=unaccent('%s'))

            where_clause_params += [search_name] * 10
            if limit:
                query += ' limit %s'
                where_clause_params.append(limit)
            self.env.cr.execute(query, where_clause_params)
            partner_ids = map(lambda x: x[0], self.env.cr.fetchall())

            if partner_ids:
                return self.browse(partner_ids).tgl_name_get()
            else:
                return []
        return self.search(args, limit=limit).tgl_name_get()
    

    
    @api.multi
    def tgl_name_get(self):
        res = []
        for partner in self:
            name = partner.name or ''
            if partner.mobile:
                name += ' | ' + partner.mobile
            if partner.mobile2:
                name += ' | ' + partner.mobile2
            if partner.mobile3:
                name += ' | ' + partner.mobile3
            elif partner.phone:
                name += ' | ' + partner.phone
            if partner.email:
                name += ' | ' + partner.email
            if partner.comment:
                name += ' | ' + partner.comment
            res.append((partner.id, name))
        return res

    # def name_get(self):
    #     res = []
    #     for partner in self:
    #         name = partner.name or ''
    #         if partner.mobile:
    #             name += ' | ' + partner.mobile
    #         if partner.mobile2:
    #             name += ' | ' + partner.mobile2
    #         if partner.mobile3:
    #             name += ' | ' + partner.mobile3
    #         elif partner.phone:
    #             name += ' | ' + partner.phone
    #         if partner.email:
    #             name += ' | ' + partner.email
    #         if partner.comment:
    #             name += ' | ' + partner.comment
    #         res.append((partner.id, name))
    #     return res

    @api.depends('mobile','phone','mobile2')#'mobile2','mobile3')
    def _compute_display_name(self):
        super(ResPartner,self)._compute_display_name()
        # diff = dict(show_address=None, show_address_only=None, show_email=None, html_format=None, show_vat=False)
        # names = dict(self.with_context(**diff).name_get())
        # for partner in self:
        #     partner.display_name = names.get(partner.id)


    def dc_name_gen(self):
        partner = self
        name = partner.name or ''
        if partner.mobile:
            name += ' | ' + partner.mobile
        if partner.mobile2:
            name += ' | ' + partner.mobile2
        if partner.mobile3:
            name += ' | ' + partner.mobile3
        elif partner.phone:
            name += ' | ' + partner.phone
        if partner.email:
            name += ' | ' + partner.email
        if partner.comment:
            name += ' | ' + partner.comment
        return name
    
    def _get_contact_name(self, partner, name):
        name = self.dc_name_gen()
        return "%s, %s" % (partner.commercial_company_name or partner.parent_id.name, name)

    # def _get_name(self): #origin là như vậy
    #     """ Utility method to allow name_get to be overrided without re-browse the partner """
    #     partner = self
    #     name = partner.name or ''

    #     if partner.company_name or partner.parent_id:
    #         if not name and partner.type in ['invoice', 'delivery', 'other']:
    #             name = dict(self.fields_get(['type'])['type']['selection'])[partner.type]
    #         if not partner.is_company:
    #             name = self._get_contact_name(partner, name)
    #     if self._context.get('show_address_only'):
    #         name = partner._display_address(without_company=True)
    #     if self._context.get('show_address'):
    #         name = name + "\n" + partner._display_address(without_company=True)
    #     name = name.replace('\n\n', '\n')
    #     name = name.replace('\n\n', '\n')
    #     if self._context.get('address_inline'):
    #         name = name.replace('\n', ', ')
    #     if self._context.get('show_email') and partner.email:
    #         name = "%s <%s>" % (name, partner.email)
    #     if self._context.get('html_format'):
    #         name = name.replace('\n', '<br/>')
    #     if self._context.get('show_vat') and partner.vat:
    #         name = "%s ‒ %s" % (name, partner.vat)
    #     return name
    
