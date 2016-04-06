# -*- coding: utf-8 -*-
# Copyright (c) 2015, bobzz.zone@gmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cstr, flt, cint, nowdate, add_days, comma_and
from frappe.model.document import Document

from frappe import msgprint, _

class PurchaseTool(Document):
	def get_po(self):
		data = frappe.db.sql("""select si.item_code,si.item_name,sum(si.qty)
from `tabSales Invoice Item` si join `tabSales Invoice` s on si.parent=s.name join `tabItem` i on  si.item_code = i.name
where i.default_supplier="{}" and s.posting_date between "{}" and "{}"
group by si.item_code """.format(self.supplier,self.from_date,self.to_date),as_list=1)
		self.items=[]
		for row in data:
			item = self.append("items",{})
			item.item_code=row[0]
			item.item_name=row[1]
			item.qty=row[2]
	def create_po(self):
		if not self.items or len(self.items)==0:
			frappe.throw("No data")
		#msgprint(len(self.items))
		supplier = frappe.get_doc("Supplier",{"name":self.supplier})
		purchase_order = frappe.new_doc("Purchase Order")
		purchase_order.update({
			"transaction_date":nowdate(),
			"status":"Draft",
			"supplier":self.supplier,
			"supplier_name":supplier.supplier_name
		})
		item_list = frappe.db.sql("""select si.item_code,si.item_name,sum(si.qty)
from `tabSales Invoice Item` si join `tabSales Invoice` s on si.parent=s.name join `tabItem` i on  si.item_code = i.name
where i.default_supplier="{}" and s.posting_date between "{}" and "{}"
group by si.item_code """.format(self.supplier,self.from_date,self.to_date),as_list=1)
		for data in item_list:
			id = frappe.get_doc("Item",{"item_code":data[0]})
			purchase_order.append("items",{
				"doctype":"Purchase Order Item",
				"__isLocal":1,
				"item_code":data[0],
				"item_name":data[1],
				"description":id.description,
				"item_group":id.item_group,
				"uom":id.stock_uom,
				"brand":id.brand,
				"qty":data[2],
				"schedule_date":nowdate(),
				"stock_uom":id.stock_uom,
				"conversion_factor":1,
				"base_rate":0,
				"base_amount":0,
				"warehouse":id.default_warehouse
			})
		purchase_order.save()
		msgprint("PO Created {}".format(purchase_order.name))
