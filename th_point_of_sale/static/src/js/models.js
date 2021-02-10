odoo.define('th_point_of_sale.models', function (require) {
    "use strict";

    var core = require('web.core');
    var models = require('point_of_sale.models');
    var utils = require('web.utils');

    var round_di = utils.round_decimals;
    var round_pr = utils.round_precision;

    models.load_fields("pos.category", ['font_color', 'background_color']);
    models.load_fields("product.product", ['is_menu_item', 'is_menu_combo', 'menu_categ_id',
                                           'modifier_group_id', 'void_require_approval',
                                           'product_ingredient_ids', 'combo_menu_ids',
                                           'special_modifier_ids', 'smart_select_id', 'outlet_standard_price', 'primary_menu_in_combo_ids']);
    models.load_fields("res.company", ['pos_footer_mesage']);
    // Load: Menu Category
    models.load_models({
        model: 'th.menu.category',
        fields: ['id', 'name', 'parent_id', 'sequence'],
        loaded: function(self, menu_categories) {
            var menu_categ_by_id = {};
            _.each(menu_categories, function (category) {
                menu_categ_by_id[category.id] = category;
            });
            _.each(menu_categories, function (category) {
                category.parent = menu_categ_by_id[category.parent_id[0]];
            });

            self.menu_categories = menu_categories;
        },
    });

    // Load: Modifier Group
    models.load_models({
        model: 'th.modifier.group',
        fields: ['id', 'name', 'sequence', 'product_option_ids', 'modifier_option_ids',
            'display_on_receipt', 'allow_multiple_selection', 'max_selection'],
        loaded: function(self, modifier_groups) {
            var modifier_grp_by_id = {};
            _.each(modifier_groups, function (group) {
                modifier_grp_by_id[group.id] = group;
            });

            self.modifier_groups = modifier_groups;
        },
    });

    // Load: TH Menu Product
    models.load_models({
        model: 'th.menu.product',
        fields: ['id', 'sequence', 'default_menu_for_combo',
            'product_id', 'pos_categ_id', 'max_selection', 'min_selection',
            'allow_substitution', 'cheaper_substitution', 'auto_compute_surcharge',
            'fixed_surcharge', 'menu_upsell_ids'],
        loaded: function(self, all_menus_for_combo) {
            self.all_menus_for_combo = all_menus_for_combo;
        },
    });

    // Load: TH Menu UpSell
    models.load_models({
        model: 'th.menu.upsell',
        fields: ['id', 'sequence', 'pos_categ_id', 'auto_compute_surcharge',
            'fixed_surcharge', 'from_date', 'to_date'],
        loaded: function(self, all_menus_for_upsell) {
            self.all_menus_for_upsell = all_menus_for_upsell;
        },
    });

    // Load: TH Ingredient Product
    models.load_models({
        model: 'th.ingredient.product',
        fields: ['id', 'product_id', 'qty', 'recovery',
            'optional', 'show_in_cart', 'modifier_group_ids'],
        loaded: function(self, all_ingredients) {
            var ingredient_by_id = {};
            _.each(all_ingredients, function (ingredient) {
                ingredient_by_id[ingredient.id] = ingredient;
            });
            self.all_ingredients = all_ingredients;
        },
    });

    // Load: Th Modifier Product
    models.load_models({
        model: 'th.modifier.product',
        fields: ['id', 'modifier_id', 'special_modifier_id', 'product_id', 'code_name',
            'qty', 'recovery', 'qty_multiplier', 'font_color', 'background_color',
            'extra_price', 'max_selection_qty'],
        loaded: function(self, all_modifiers) {
            var modifier_by_id = {};
            _.each(all_modifiers, function (modifier) {
                modifier_by_id[modifier.id] = modifier;
            });
            self.all_modifiers = all_modifiers;
        },
    });

    // Load: Th Modifier Options
    models.load_models({
        model: 'th.modifier.options',
        fields: ['id', 'name', 'is_basic', 'special_modifier', 'remove_extra',
            'qty_multiplier', 'price_multiplier'],
        loaded: function(self, all_modifiers_options) {
            var modifier_option_by_id = {};
            _.each(all_modifiers_options, function (option) {
                modifier_option_by_id[option.id] = option;
            });
            self.all_modifiers_options = all_modifiers_options;
        },
    });

    // Load: Th Special Modifier Options
    models.load_models({
        model: 'th.special.modifier.options',
        fields: ['id', 'menu_id', 'modifier_option_id', 'modifier_product_ids',
            'font_color', 'background_color'],
        loaded: function(self, special_modifiers_options) {
            var special_modifier_by_menu_id = {};
            _.each(special_modifiers_options, function (option) {
                special_modifier_by_menu_id[option.id] = option;
            });
            self.special_modifiers_options = special_modifiers_options;
        },
    });

    // Load: TH Smart Select
    models.load_models({
        model: 'th.smart.select',
        fields: ['id', 'name', 'smart_menu_ids'],
        loaded: function(self, all_smart_select) {
            self.all_smart_select = all_smart_select;
        },
    });

    // Load: TH Smart Select Lines
    models.load_models({
        model: 'th.smart.select.line',
        fields: ['id', 'sequence', 'smart_select_id', 'product_id',
            'smart_label_id', 'show_in_pos', 'font_color', 'background_color'],
        loaded: function(self, all_smart_select_menus) {
            self.all_smart_select_menus = all_smart_select_menus;
        },
    });

    // Load: TH Time Range
    models.load_models({
        model: 'th.time.range',
        fields: ['id', 'name', 'start_time', 'end_time'],
        loaded: function(self, all_time_range) {
            self.all_time_range = all_time_range;
        },
    });

    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({

        set_quantity: function(quantity, keep_price){
            var self = this;
            this.order.assert_editable();
            if (quantity === 'remove') {
                if (self.get_product().void_require_approval) {
                    // Open wizard to select manager & enter password
                    self.pos.gui.select_user({
                        'security':       true,
                        'only_managers':  true,
                        'current_user':   false,
                        'title':          _t('Only managers can remove order-line!'),
                    }).then(function(user) {
                        self.order.remove_orderline(self);
                    });
                } else {
                    self.order.remove_orderline(self);
                }
                return;
            }
            _super_orderline.set_quantity.apply(this, arguments);
        },

        // Do not merge line if product is Menu/Combo
        can_be_merged_with: function(orderline) {
            if (orderline.product.is_menu_item) {
                return false;
            } else {
                return _super_orderline.can_be_merged_with.apply(this, arguments);
            }
        },

        // Override & pass menu_datas
        export_as_JSON: function() {
            var pack_lot_ids = [];
            if (this.has_product_lot){
                this.pack_lot_lines.each(_.bind( function(item) {
                    return pack_lot_ids.push([0, 0, item.export_as_JSON()]);
                }, this));
            }
            return {
                qty: this.get_quantity(),
                price_unit: this.get_unit_price(),
                price_subtotal: this.get_price_without_tax(),
                price_subtotal_incl: this.get_price_with_tax(),
                discount: this.get_discount(),
                product_id: this.get_product().id,
                tax_ids: [[6, false, _.map(this.get_applicable_taxes(), function(tax){ return tax.id; })]],
                id: this.id,
                pack_lot_ids: pack_lot_ids,
                menu_datas: this.menu_datas
            };
        },
    });

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        export_as_JSON: function() {
            var self = this;
            var orderLines, paymentLines, ingredientLines;
            orderLines = [];
            this.orderlines.each(_.bind( function(item) {
                // Pass the dummy menu lines for Combo with no value(s)
                // @todo Need to pass the correct qty which comes from Combo Configuration instead of 1.0
                if (item.is_combo) {
                    orderLines.push([0, 0, item.export_as_JSON()]);
                    var menu_datas = [];
                    _.each(item.menus, function(menu) {
                        menu_datas.push([0, 0, {
                            qty: 1.0,
                            price_unit: 0.0,
                            price_subtotal: 0.0,
                            price_subtotal_incl: 0.0,
                            discount: 0.0,
                            product_id: menu.product_id[0],
                            tax_ids: false,
                            id: item.id,
                            pack_lot_ids: false
                        }]);
                    });
                    item.menu_datas = menu_datas;
                    return;
                } else {
                    return orderLines.push([0, 0, item.export_as_JSON()]);
                }
            }, this));

            ingredientLines = [];
            var rounding = this.pos.currency.rounding;
            this.orderlines.each(_.bind( function(line) {
                _.each(line.ingredients, function(ingredient) {
                    var extra_price = (ingredient.qty * line.get_quantity()) * ingredient.extra_price;
                    ingredientLines.push([0, 0, {
                        'is_extra': ingredient.is_extra,
                        'menu_id': ingredient.menu_id,
                        'product_id': ingredient.product_id[0],
                        'qty': ingredient.qty * line.get_quantity(),
                        'recovery': ingredient.recovery,
                        'price_unit': round_pr(extra_price, rounding),
                        'id': ingredient.id,
                        'standard_price': self.pos.db.get_product_by_id(ingredient.product_id[0]).outlet_standard_price,
                    }]);
                })
            }));

            paymentLines = [];
            this.paymentlines.each(_.bind( function(item) {
                return paymentLines.push([0, 0, item.export_as_JSON()]);
            }, this));

            return {
                name: this.get_name(),
                amount_paid: this.get_total_paid() - this.get_change(),
                amount_total: this.get_total_with_tax(),
                amount_tax: this.get_total_tax(),
                amount_return: this.get_change(),
                ingredient_lines: ingredientLines,
                lines: orderLines,
                statement_ids: paymentLines,
                pos_session_id: this.pos_session_id,
                pricelist_id: this.pricelist ? this.pricelist.id : false,
                partner_id: this.get_client() ? this.get_client().id : false,
                user_id: this.pos.get_cashier().id,
                uid: this.uid,
                sequence_number: this.sequence_number,
                creation_date: this.validation_date || this.creation_date, // todo: rename creation_date in master
                fiscal_position_id: this.fiscal_position ? this.fiscal_position.id : false,
                to_invoice: this.to_invoice ? this.to_invoice : false,
            };
        },
    });

});
