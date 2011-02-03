# -*- coding: utf-8 -*-
from __future__ import with_statement
from decimal import Decimal
from django.contrib.auth.models import User
from shop.cart.modifiers_pool import cart_modifiers_pool
from shop.models.cartmodel import Cart, CartItem
from shop.models.clientmodel import Client, Address, Country
from shop.models.ordermodel import Order, OrderItem, ExtraOrderPriceField
from shop.models.productmodel import Product
from shop.tests.utils.context_managers import SettingsOverride
from unittest import TestCase

class OrderTestCase(TestCase):
    
    PRODUCT_PRICE = Decimal('100')
    TEN_PERCENT = Decimal(10) / Decimal(100)
    
    def setUp(self):
        
        cart_modifiers_pool.USE_CACHE=False
        
        self.user = User.objects.create(username="test", email="test@example.com")
        
        self.product = Product()
        self.product.name = "TestPrduct"
        self.product.slug = "TestPrduct"
        self.product.short_description = "TestPrduct"
        self.product.long_description = "TestPrduct"
        self.product.active = True
        self.product.unit_price = self.PRODUCT_PRICE
        self.product.save()
        
        self.cart = Cart()
        self.cart.user = self.user
        self.cart.save()
        
        self.client = Client()
        self.client.user = self.user
        self.client.save()
        
        self.country = Country.objects.create(name='CH')
        
        self.address = Address()
        self.address.client = self.client
        self.address.address = 'address'
        self.address.address2 = 'address2'
        self.address.zip_code = '1234'
        self.address.state = 'ZH'
        self.address.country = self.country
        self.address.is_billing = True
        self.address.is_shipping = True
        self.address.save()
        
    
    def tearDown(self):
        self.user.delete()
        self.product.delete()
    
    def test_01_create_order_from_simple_cart(self):
        '''
        Let's make sure that all the info is copied over properly when using
        Order.objects.create_from_cart()
        '''
        self.cart.add_product(self.product)
        self.cart.update()
        self.cart.save()
        
        o = Order.objects.create_from_cart(self.cart)
        
        self.assertNotEqual(o, None)
        
        ois = OrderItem.objects.filter(order=o)
        cis = CartItem.objects.filter(cart=self.cart)
        self.assertEqual(len(ois), len(cis))
        
        self.assertEqual(o.order_subtotal, self.cart.subtotal_price)
        self.assertEqual(o.order_total, self.cart.total_price)

    def test_02_create_order_from_taxed_cart(self):
        '''
        This time assert that everything is consistent with a tax cart modifier
        '''
        MODIFIERS = ['shop.cart.modifiers.tax_modifiers.TenPercentTaxModifier']
        
        with SettingsOverride(SHOP_PRICE_MODIFIERS=MODIFIERS):

            self.cart.add_product(self.product)
            self.cart.update()
            self.cart.save()
            
            o = Order.objects.create_from_cart(self.cart)
            
            # Must not return None, obviously
            self.assertNotEqual(o, None)
            
            # Compare all the OrderItems to all CartItems (length)
            ois = OrderItem.objects.filter(order=o)
            cis = CartItem.objects.filter(cart=self.cart)
            self.assertEqual(len(ois), len(cis))
            
            # Assert that there are as many extra_cart_price_fields than there
            # are extra order price fields
            e_cart_fields = self.cart.extra_price_fields
            e_order_fields = ExtraOrderPriceField.objects.filter(order=o)
            self.assertEqual(len(e_cart_fields), len(e_order_fields))
            
            # Check that totals match
            self.assertEqual(o.order_subtotal, self.cart.subtotal_price)
            self.assertEqual(o.order_total, self.cart.total_price)
                
        