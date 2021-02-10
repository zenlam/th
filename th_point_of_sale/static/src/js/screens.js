odoo.define('th_point_of_sale.screens', function (require) {
    "use strict";

    var core = require('web.core');
    var PosBaseWidget = require('point_of_sale.BaseWidget');
    var screens = require('point_of_sale.screens');

    var QWeb = core.qweb;
    var _t = core._t;

    // Store the `product_categories_widget` inside global namespace
    var PRODUCT_CATEGORIES_WIDGET;

    // Store the `top_selling_menus_widget` inside global namespace
    var TOP_SELLING_MENUS_WIDGET;

    screens.ProductCategoriesWidget.include({

        init: function(parent, options) {
            var self = this;
            this._super(parent,options);
            this.sub_category_structure = false;
        },

        renderElement: function() {
            var self = this;
            var el_str  = QWeb.render(this.template, {widget: this});
            var el_node = document.createElement('div');

            el_node.innerHTML = el_str;
            el_node = el_node.childNodes[1];

            if(this.el && this.el.parentNode){
                this.el.parentNode.replaceChild(el_node,this.el);
            }

            this.el = el_node;
            var withpics = this.pos.config.iface_display_categ_images;
            var list_container = el_node.querySelector('.category-list');

            /**
             *  Section to load all the sub-categories with multi-level support
             */
            var list_container_all_sub = el_node.querySelector('.category-list-all-sub');

            if (list_container) {
                if (!withpics) {
                    list_container.classList.add('simple');
                } else {
                    list_container.classList.remove('simple');
                }
                if (this.category.id == 0) {
                    for(var i = 0, len = this.subcategories.length; i < len; i++){
                        list_container.appendChild(this.render_category(this.subcategories[i],withpics));
                    }
                } else {
                    /**
                     *  Even current active category is not "Root"
                     *  We display all Parent(1st level) Category, which have "Root" category as Parent
                     */
                    var root_category_ids = this.pos.db.get_category_childs_ids(0);
                    for(var i = 0, len = root_category_ids.length; i < len; i++){
                        list_container.appendChild(this.render_category(
                        this.pos.db.get_category_by_id(root_category_ids[i]),withpics));
                    }

                    if (list_container_all_sub) {

                        var active_category = this.category.id;
                        var parent_of_active_category = this.pos.db.get_category_parent_id(this.category.id);
                        var child_of_active_category = this.pos.db.get_category_childs_ids(this.category.id);

                        self.checkParentRecursive(list_container_all_sub, active_category,
                                                  parent_of_active_category, child_of_active_category, withpics);

                        if (child_of_active_category.length > 0) {
                            var list_container_sub = document.createElement('div');
                            list_container_sub.classList.add('category-list-sub');
                            if (!withpics) {
                                list_container_sub.classList.add('simple');
                            } else {
                                list_container_sub.classList.remove('simple');
                            }
                            for(var i = 0, len = child_of_active_category.length; i < len; i++){
                                list_container_sub.appendChild(this.render_category(
                                this.pos.db.get_category_by_id(child_of_active_category[i]),withpics));
                            }
                            list_container_all_sub.appendChild(list_container_sub);
                        }
                    }
                }
            }

            var buttons = el_node.querySelectorAll('.js-category-switch');
            for(var i = 0; i < buttons.length; i++){
                buttons[i].addEventListener('click',this.switch_category_handler);
            }

            var products = this.pos.db.get_product_by_category(this.category.id);

            // Get products/menus according to active price list
            var current_pricelist = this.product_list_widget._get_active_pricelist();
            var product_lst = [];
            _.each(current_pricelist.items, function(item) {
                if (item.time_range_ids.length > 0) {
                    var d = new Date(),
                        h = d.getHours(),
                        m = d.getMinutes();
                    var hm_decimal = h + m / 60;
                    var time_range = _.filter(self.pos.all_time_range, function(tr) {
                        return _.contains(item.time_range_ids, tr.id);
                    });
                    _.each(time_range, function(range) {
                        if (item.product_id && hm_decimal >= range.start_time && hm_decimal < range.end_time) {
                            product_lst.push(item.product_id[0]);
                        }
                    });
                } else {
                    if (item.product_id) {
                        product_lst.push(item.product_id[0]);
                    }
                }
            });

            // Filter products/menus for Smart Select which are hidden in POS Screen
            var hidden_smart_prods = [];
            _.each(products, function(product) {
                if (product.smart_select_id) {
                    _.each(self.pos.all_smart_select_menus, function(s_menu) {
                        if ((product.smart_select_id[0] === s_menu.smart_select_id[0]) && !s_menu.show_in_pos) {
                            hidden_smart_prods.push(s_menu.product_id[0]);
                        }
                    });
                }
            });

            product_lst = _.difference(product_lst, _.uniq(hidden_smart_prods));

            // Filter products/menus
            products = _.filter(products, function(product) {
                return _.contains(product_lst, product.id);
            });

            this.product_list_widget.set_product_list(products); // FIXME: this should be moved elsewhere ...

            if (arguments[0]) {
                // Still keeps space above for Smart Selection if those are still active
                $('div.product-list-container').css({'top': '40px'});
            } else {
                // Empty the smart select space if any
                $('div.product-list-container').css({'top': '0px'});
                $('div.placeholder-SmartSelectWidget').empty();
            }

            if (arguments[1]) {
                // Keep product list hidden, if modify combo screen is active
                $('div.product-list-container').addClass('oe_hidden');
            } else {
                // Empty the combo list widget space if any
                $('div.placeholder-ComboListWidget').empty();
                $('div.product-list-container').removeClass('oe_hidden');
            }

            this.el.querySelector('.searchbox input').addEventListener('keypress',this.search_handler);

            this.el.querySelector('.searchbox input').addEventListener('keydown',this.search_handler);

            this.el.querySelector('.search-clear').addEventListener('click',this.clear_search_handler);

            if(this.pos.config.iface_vkeyboard && this.chrome.widget.keyboard){
                this.chrome.widget.keyboard.connect($(this.el.querySelector('.searchbox input')));
            }

            /**
             *  Highlight Active Categories
             */
            var list_of_active_categ = el_node.querySelectorAll('.breadcrumb-button');
            var all_visible_categ = el_node.querySelectorAll('.categories .js-category-switch');

            _.each(all_visible_categ, function(each_categ) {
                $(each_categ).find('i.fa-fw').addClass('oe_hidden');
            });

            _.each(list_of_active_categ, function(active_categ) {
                var active_categ_id = active_categ.getAttribute('data-category-id');
                _.each(all_visible_categ, function(each_categ) {
                    if (each_categ.getAttribute('data-category-id') === active_categ_id) {
                        $(each_categ).find('i.fa-fw').removeClass('oe_hidden');
                    }
                });
            });
        },

        checkParentRecursive: function(list_container_all_sub,
                                       active_category, parent_of_active_category,
                                       child_of_active_category, withpics) {
            var self = this;
            if (parent_of_active_category != 0) {
                var list_container_sub = document.createElement('div');
                list_container_sub.classList.add('category-list-sub');
                if (!withpics) {
                    list_container_sub.classList.add('simple');
                } else {
                    list_container_sub.classList.remove('simple');
                }

                var parent_category_level = self.pos.db.get_category_childs_ids(parent_of_active_category);

                for(var i = 0, len = parent_category_level.length; i < len; i++) {
                    list_container_sub.appendChild(self.render_category(
                    self.pos.db.get_category_by_id(parent_category_level[i]),withpics));
                }
                list_container_all_sub.insertBefore(list_container_sub, list_container_all_sub.firstChild);

                var active_category = parent_of_active_category;
                var parent_of_active_category = self.pos.db.get_category_parent_id(parent_of_active_category);
                var child_of_active_category = self.pos.db.get_category_childs_ids(parent_of_active_category);

                self.checkParentRecursive(list_container_all_sub, active_category,
                                     parent_of_active_category, child_of_active_category, withpics);
            }
        },

        // empties the content of the search box
        clear_search: function(){
            var self = this;
            var products = this.pos.db.get_product_by_category(this.category.id);

            // Empty the smart select space if any
            $('div.product-list-container').css({'top': '0px'});
            $('div.placeholder-SmartSelectWidget').empty();

            // Get products/menus according to active price list
            var current_pricelist = this.product_list_widget._get_active_pricelist();
            var product_lst = [];
            _.each(current_pricelist.items, function(item) {
                if (item.time_range_ids.length > 0) {
                    var d = new Date(),
                        h = d.getHours(),
                        m = d.getMinutes();
                    var hm_decimal = h + m / 60;
                    var time_range = _.filter(self.pos.all_time_range, function(tr) {
                        return _.contains(item.time_range_ids, tr.id);
                    });
                    _.each(time_range, function(range) {
                        if (item.product_id && hm_decimal >= range.start_time && hm_decimal < range.end_time) {
                            product_lst.push(item.product_id[0]);
                        }
                    });
                } else {
                    if (item.product_id) {
                        product_lst.push(item.product_id[0]);
                    }
                }
            });

            // Filter products/menus for Smart Select which are hidden in POS Screen
            var hidden_smart_prods = [];
            _.each(products, function(product) {
                if (product.smart_select_id) {
                    _.each(self.pos.all_smart_select_menus, function(s_menu) {
                        if ((product.smart_select_id[0] === s_menu.smart_select_id[0]) && !s_menu.show_in_pos) {
                            hidden_smart_prods.push(s_menu.product_id[0]);
                        }
                    });
                }
            });

            product_lst = _.difference(product_lst, _.uniq(hidden_smart_prods));

            // Filter products/menus
            products = _.filter(products, function(product) {
                return _.contains(product_lst, product.id);
            });

            this.product_list_widget.set_product_list(products);

            var input = this.el.querySelector('.searchbox input');
                input.value = '';
                input.focus();
        },

        perform_search: function(category, query, buy_result){
            var self = this;
            var products;

            // Empty the smart select space if any
            $('div.product-list-container').css({'top': '0px'});
            $('div.placeholder-SmartSelectWidget').empty();

            if(query){
                products = this.pos.db.search_product_in_category(category.id,query);

                // Get products/menus according to active price list
                var current_pricelist = this.product_list_widget._get_active_pricelist();
                var product_lst = [];
                _.each(current_pricelist.items, function(item) {
                    if (item.time_range_ids.length > 0) {
                        var d = new Date(),
                            h = d.getHours(),
                            m = d.getMinutes();
                        var hm_decimal = h + m / 60;
                        var time_range = _.filter(self.pos.all_time_range, function(tr) {
                            return _.contains(item.time_range_ids, tr.id);
                        });
                        _.each(time_range, function(range) {
                            if (item.product_id && hm_decimal >= range.start_time && hm_decimal < range.end_time) {
                                product_lst.push(item.product_id[0]);
                            }
                        });
                    } else {
                        if (item.product_id) {
                            product_lst.push(item.product_id[0]);
                        }
                    }
                });

                // Filter products/menus for Smart Select which are hidden in POS Screen
                var hidden_smart_prods = [];
                _.each(products, function(product) {
                    if (product.smart_select_id) {
                        _.each(self.pos.all_smart_select_menus, function(s_menu) {
                            if ((product.smart_select_id[0] === s_menu.smart_select_id[0]) && !s_menu.show_in_pos) {
                                hidden_smart_prods.push(s_menu.product_id[0]);
                            }
                        });
                    }
                });

                product_lst = _.difference(product_lst, _.uniq(hidden_smart_prods));

                // Filter products/menus
                products = _.filter(products, function(product) {
                    return _.contains(product_lst, product.id);
                });

                if(buy_result && products.length === 1){
                        this.pos.get_order().add_product(products[0]);
                        this.clear_search();
                }else{
                    this.product_list_widget.set_product_list(products);
                }
            } else {
                products = this.pos.db.get_product_by_category(this.category.id);

                // Get products/menus according to active price list
                var current_pricelist = this.product_list_widget._get_active_pricelist();
                var product_lst = [];
                _.each(current_pricelist.items, function(item) {
                    if (item.time_range_ids.length > 0) {
                        var d = new Date(),
                            h = d.getHours(),
                            m = d.getMinutes();
                        var hm_decimal = h + m / 60;
                        var time_range = _.filter(self.pos.all_time_range, function(tr) {
                            return _.contains(item.time_range_ids, tr.id);
                        });
                        _.each(time_range, function(range) {
                            if (item.product_id && hm_decimal >= range.start_time && hm_decimal < range.end_time) {
                                product_lst.push(item.product_id[0]);
                            }
                        });
                    } else {
                        if (item.product_id) {
                            product_lst.push(item.product_id[0]);
                        }
                    }
                });

                // Filter products/menus for Smart Select which are hidden in POS Screen
                var hidden_smart_prods = [];
                _.each(products, function(product) {
                    if (product.smart_select_id) {
                        _.each(self.pos.all_smart_select_menus, function(s_menu) {
                            if ((product.smart_select_id[0] === s_menu.smart_select_id[0]) && !s_menu.show_in_pos) {
                                hidden_smart_prods.push(s_menu.product_id[0]);
                            }
                        });
                    }
                });

                product_lst = _.difference(product_lst, _.uniq(hidden_smart_prods));

                // Filter products/menus
                products = _.filter(products, function(product) {
                    return _.contains(product_lst, product.id);
                });

                this.product_list_widget.set_product_list(products);
            }
        },

    });

    /* ------------ Top Selling Menus Widget ------------ */
    var TopSellingWidget = PosBaseWidget.extend({
        template: 'TopSellingWidget',
        init: function(parent) {
            this._super(parent);
        },

        renderElement: function() {
            var self = this;
            var current_order = this.pos.get_order();
            var current_pricelist = this.pos.default_pricelist;
            if (current_order) {
                current_pricelist = current_order.pricelist;
            }

            var active_outlet = _.find(this.pos.all_outlet, function(outlet) {
                return self.pos.config.outlet_id[0] === outlet.id;
            });

            var pricelist_prods = [];
            _.each(current_pricelist.items, function(item) {
                pricelist_prods.push(item.product_id[0]);
            });

            var top_menus = [];
            _.each(active_outlet.top_selling_menu_ids, function(menu) {
                if (_.contains(pricelist_prods, menu)) {
                    top_menus.push(self.pos.db.get_product_by_id(menu));
                }
            });

            this.top_selling_menus = top_menus;
            this.current_pricelist = current_pricelist;
            this._super();

            this.$('.top-selling-menu').click(function(ev) {
                var product_id = $(ev.target).data('menu-id');
                if (!product_id) {
                    product_id = $(ev.target).parent().data('menu-id');
                }
                var order = self.pos.get_order();
                var product = self.pos.db.get_product_by_id(product_id);
                order.add_product(product, {quantity: 1, merge: false});
            });
        },
    });

    screens.ActionpadWidget.include({
        init: function(parent, options) {
            var self = this;
            this._super(parent, options);

            // Re-init Pricelist widget
            this.widget_pricelist = new screens.set_pricelist_button(self, {});
        },

        start: function() {
            var self = this;
            this._super();
            this.top_selling_menus_widget = new TopSellingWidget(this, {});
            this.top_selling_menus_widget.replace($('div.placeholder-TopSellingWidget'));
            TOP_SELLING_MENUS_WIDGET = this.top_selling_menus_widget;
        },

        renderElement: function() {
            var self = this;
            this._super();

            this.$('.multi-func-pad').click(function() {
                self.gui.show_popup('numpad_popup', {
                    'title': _t('Quantity Keypad'),
                });
            });

            this.$('.repeat-orderline').click(function() {
                var order = self.pos.get_order();
                var selected_orderline = order.get_selected_orderline();
                if(selected_orderline) {
                    /**
                     *  ``merge: false``
                     *  Do not merge repeat order-line with existing one.
                     */
                    var product = selected_orderline.product;
                    order.add_product(product, {quantity: 1, merge: false});
                }
            });

            this.$('.o_pricelist_button_dummy').click(function() {
                self.widget_pricelist.button_click();
            });

            this.$('.enables-more-functions').click(function() {
                self.gui.show_popup('function_popup');
            });
        },
    });

    screens.OrderWidget.include({
        // Get the information related to ingredients, modifiers, etc...
        th_misc_details: function(orderline, for_combo=false) {
            var self = this;

            if (!for_combo) {
                orderline.ingredients_show = [];
                var ingredients_opts = [];
                var modifiers_grps = [];
                _.each(orderline.ingredients, function(ingredient) {
                    // Show default ingredient if orderline is not combo
                    if (ingredient.show_in_cart) {
                        orderline.ingredients_show.push(ingredient);
                    }
                    if (!orderline.get_product().is_menu_combo) {
                        ingredient.menu_id = orderline.get_product().id;
                    }
                    ingredient.is_extra = false;
                    ingredient.extra_price = 0;
                    if (ingredient.optional) {
                        modifiers_grps.push(ingredient.modifier_group_ids);
                    }
                });

                var flatten_modifiers_grps = _.flatten(modifiers_grps)
                var uniq_modifiers_grps = _.uniq(flatten_modifiers_grps);

                var modifier_grps_for_opts = _.filter(self.pos.modifier_groups, function(mod) {
                    return _.contains(uniq_modifiers_grps, mod.id);
                });

                //Add modifier opts inside `self.pos.all_modifiers`
                _.each(self.pos.all_modifiers, function(mod) {
                    _.each(modifier_grps_for_opts, function(grp_opts) {
                        if (mod.modifier_id[0] === grp_opts.id) {
                            mod.modifier_option_ids = grp_opts.modifier_option_ids;
                            mod.allow_multiple_selection = grp_opts.allow_multiple_selection;
                            mod.max_selection = grp_opts.max_selection;

                            ingredients_opts.push(grp_opts.modifier_option_ids);
                        }
                    });
                });

                var flatten_ingredients_opts = _.flatten(ingredients_opts)
                var uniq_ingredients_opts = _.uniq(flatten_ingredients_opts);

                orderline.modifiers_opts = _.filter(self.pos.all_modifiers_options, function(mod_opt) {
                    return _.contains(uniq_ingredients_opts, mod_opt.id);
                });

                var modifiers = _.filter(self.pos.all_modifiers, function(modifier) {
                    return _.contains(uniq_modifiers_grps, modifier.modifier_id[0]);
                });

                orderline.modifiers_by_grp = _.groupBy(modifiers, function(line) {
                    return line.modifier_id[1];
                });

                // Find the default ingredient & marked it for future reference
                _.filter(orderline.modifiers_by_grp, function(grp) {
                    return _.each(grp, function(line) {
                        return _.find(orderline.ingredients, function(ingredient) {
                            if (line.product_id[0] === ingredient.product_id[0]) {
                                line.is_default = true;
                                line.default_qty = ingredient.qty;
                                return;
                            }
                        });
                    });
                });

                // Special Modifiers for Orderline
                orderline.special_modifiers_opts = _.filter(self.pos.special_modifiers_options, function(special_mod) {
                    return orderline.get_product().id === special_mod.menu_id[0];
                });
                _.each(orderline.special_modifiers_opts, function(special_mod) {
                    special_mod.modifier_products = _.filter(self.pos.all_modifiers, function(mod) {
                        return _.contains(special_mod.modifier_product_ids, mod.id);
                    });
                });
                orderline.special_opts_lst = [];
            } else {
                console.log("th_misc_details>>>>>>>>>COMBO>>>>>", orderline);
                var ingredients_opts = [];
                var modifiers_grps = [];
                _.each(orderline.ingredients, function(ingredient) {
                    if (ingredient.optional) {
                        modifiers_grps.push(ingredient.modifier_group_ids);
                    }
                });

                var flatten_modifiers_grps = _.flatten(modifiers_grps)
                var uniq_modifiers_grps = _.uniq(flatten_modifiers_grps);

                var modifier_grps_for_opts = _.filter(self.pos.modifier_groups, function(mod) {
                    return _.contains(uniq_modifiers_grps, mod.id);
                });

                //Add modifier opts inside `self.pos.all_modifiers`
                _.each(self.pos.all_modifiers, function(mod) {
                    _.each(modifier_grps_for_opts, function(grp_opts) {
                        if (mod.modifier_id[0] === grp_opts.id) {
                            mod.modifier_option_ids = grp_opts.modifier_option_ids;
                            mod.allow_multiple_selection = grp_opts.allow_multiple_selection;
                            mod.max_selection = grp_opts.max_selection;

                            ingredients_opts.push(grp_opts.modifier_option_ids);
                        }
                    });
                });

                var flatten_ingredients_opts = _.flatten(ingredients_opts)
                var uniq_ingredients_opts = _.uniq(flatten_ingredients_opts);

                orderline.modifiers_opts = _.filter(self.pos.all_modifiers_options, function(mod_opt) {
                    return _.contains(uniq_ingredients_opts, mod_opt.id);
                });

                var modifiers = _.filter(self.pos.all_modifiers, function(modifier) {
                    return _.contains(uniq_modifiers_grps, modifier.modifier_id[0]);
                });

                orderline.modifiers_by_grp = _.groupBy(modifiers, function(line) {
                    return line.modifier_id[1];
                });

                // Find the default ingredient & marked it for future reference
                _.filter(orderline.modifiers_by_grp, function(grp) {
                    return _.each(grp, function(line) {
                        return _.find(orderline.ingredients, function(ingredient) {
                            if (line.product_id[0] === ingredient.product_id[0] && !ingredient.is_extra) {
                                line.is_default = true;
                                line.default_qty = ingredient.qty;
                                return;
                            }
                        });
                    });
                });
            }
        },

        load_modifiers_opts: function(orderline) {
            var self = this;
            var el_str_m = $(QWeb.render('ProductScreenWidget-Modifiers', { widget: orderline }));
            var el_node_m = $('div.placeholder-ProductScreenWidget-Modifiers').html(el_str_m);
            el_str_m.on('click', 'button.button,button.grp-special-opt-button', function() {
                self.click_on_modifier($(this), orderline);
            });
            el_str_m.on('click', 'button.grp-opt-button', function() {
                self.click_on_modifier_opts($(this));
            });
        },

        load_smart_selection: function(orderline) {
            var self = this;
            $('div.product-list-container').css({'top': '0px'});
            $('div.placeholder-SmartSelectWidget').empty();

            if (orderline.selected && orderline.get_product().smart_select_id) {
                $('div.product-list-container').css({'top': '40px'});
                var smart_select = _.find(self.pos.all_smart_select, function(rec) {
                    return rec.id === orderline.get_product().smart_select_id[0];
                });
                var smart_options = _.filter(self.pos.all_smart_select_menus, function(line) {
                    return _.contains(smart_select.smart_menu_ids, line.id);
                });

                var current_order = self.pos.get_order();
                var current_pricelist = self.pos.default_pricelist;
                if (current_order) {
                    current_pricelist = current_order.pricelist;
                }
                var pricelist_prods = [];
                _.each(current_pricelist.items, function(item) {
                    pricelist_prods.push(item.product_id[0]);
                });

                var smart_options_filter = _.filter(smart_options, function(opt) {
                    return _.contains(pricelist_prods, opt.product_id[0]);
                });

                var smart_options_sort = _.sortBy(smart_options_filter, function(opt) {
                    return opt.sequence;
                });

                var el_str_ss = $(QWeb.render('SmartSelectWidget', { widget: smart_options_sort }));
                var el_node_ss = $('div.placeholder-SmartSelectWidget').html(el_str_ss);
                $(el_str_ss).find("button[data-product-id='" + orderline.get_product().id + "'] i.active-smart-button").removeClass('oe_hidden');
                el_str_ss.on('click', '.smart-button', function() {
                    self.click_on_smart_select($(this), orderline);
                });
            }
        },

        global_update_button_badge: function(orderline) {
            // FIXME.. Bad way to display count badge but keep it for now
            // $('div.modifier-sub-section').find('button span.badge-placeholder').empty().addClass('oe_hidden');
            // $('div.modifier-sub-section').find('button span.remove-basic').addClass('oe_hidden');
            // $('div.modifier-sub-section').find('button span.basic-ingredient').removeClass('oe_hidden');

            _.each(orderline.ingredients, function(ingredient) {
                if (ingredient.is_extra) {
                    var $button = $('div.modifier-sub-section').find("button[data-product-id='" + ingredient.id + "']");
                    var new_txt = parseInt(ingredient.times_added_extra);
                    if ($button.hasClass('default-ingredient')) {
                        new_txt += 1;
                    }
                    $button.find('span.badge-placeholder').text(new_txt).removeClass('oe_hidden');
                }
            });
        },

        update_button_badge: function(ev, orderline) {
            // FIXME.. Bad way to display count badge but keep it for now
            if ($(ev).parent().hasClass('special-modifier-opt-section')) {
                console.log("FFFF");
            } else {
                $(ev).parent().find('button span.badge-placeholder').empty().addClass('oe_hidden');
                $(ev).parent().find('button span.remove-basic').addClass('oe_hidden');
                $(ev).parent().find('button span.basic-ingredient').removeClass('oe_hidden');

                _.each(orderline.ingredients, function(ingredient) {
                    if (ingredient.is_extra) {
                        _.each($(ev).parent().find('button'), function(btn) {
                            if ($(btn).data('product-id') === ingredient.id) {
                                var new_txt = parseInt(ingredient.times_added_extra);
                                if ($(btn).hasClass('default-ingredient')) {
                                    new_txt += 1;
                                }
                                $(btn).find('span.badge-placeholder').text(new_txt);
                                $(btn).find('span.badge-placeholder').removeClass('oe_hidden');
                            }
                        });
                    } else {
                        _.each($(ev).parent().find('button'), function(btn) {
                            if ($(btn).data('product-id') === ingredient.product_id[0] && ingredient.qty === 0) {
                                $(btn).find('span.remove-basic').removeClass('oe_hidden');
                                $(btn).find('span.basic-ingredient').addClass('oe_hidden');
                                $(btn).find('span.badge-placeholder').empty().addClass('oe_hidden');
                            }
                            if ($(btn).data('product-id') === ingredient.product_id[0] &&
                                $(btn).hasClass('default-ingredient') && ingredient.qty !== 0) {
                                $(btn).find('span.badge-placeholder').text('1').removeClass('oe_hidden');
                            }
                        });
                    }
                });
            }
        },

        click_on_modifier_opts: function(ev) {
            $(ev).parent().find('button.grp-opt-button').removeClass('active-opt');
            $(ev).toggleClass('active-opt');
        },

        click_on_modifier: function(ev, orderline) {
            var self = this;
            if (orderline.selected) {
                if (!$(ev).data('special-option')) {
                    // Normal Modifier
                    if (typeof($(ev).data('modifier-option-ids')) === 'string') {
                        // If multiple opts assign to grp then its string
                        var valid_opts_lst = $(ev).data('modifier-option-ids').split(',').map(Number);
                    } else {
                        // If single opts assign to grp then its number
                        var valid_opts_lst = ("" + $(ev).data('modifier-option-ids')).split('').map(Number);
                    }

                    var active_opt = $(ev).parent().parent().find('button.grp-opt-button.active-opt');
                    var active_opt_id = active_opt.data('id');

                    if (_.contains(valid_opts_lst, active_opt_id)) {
                        var qty_multiplier = $(active_opt).data('qty-multiplier'),
                            price_multiplier = $(active_opt).data('price-multiplier'),
                            remove_extra = $(active_opt).data('remove-extra'),
                            product_id = $(ev).data('product-id'),
                            product_name = $(ev).data('product-name'),
                            modifier_group_id = $(ev).data('modifier-group-id'),
                            qty = $(ev).data('qty'),
                            default_qty = $(ev).data('default-qty'),
                            extra_price = $(ev).data('extra-price'),
                            max_selection_qty = $(ev).data('max-selection-qty'),
                            allow_multiple_selection = $(ev).data('allow-multiple-selection'),
                            max_selection = $(ev).data('max-selection'),
                            recovery = parseFloat($(ev).data('recovery'));

                        // Consider as Basic Ingredient for Menu
                        var basic_ingredient = _.find(orderline.ingredients, function(line) {
                            return !line.is_extra && line.product_id[0] === product_id;
                        });

                        // Consider as Extra/Modified Ingredient for Menu
                        var extra_ingredient = _.find(orderline.ingredients, function(line) {
                            return line.is_extra && line.product_id[0] === product_id;
                        });

                        var add_default_first = false;

                        if (basic_ingredient && !remove_extra) {
                            // `NO` is the only available options which apply on basic ingredients
                            if (qty_multiplier === 0) {
                                // Means NO qty. So, do direct amend original ingredient
                                basic_ingredient.qty = basic_ingredient.qty * qty_multiplier;

                                // Remove Extra also
                                if (extra_ingredient) {
                                    // Means NO qty. So, do direct amend original ingredient
                                    extra_ingredient.qty = extra_ingredient.qty * qty_multiplier;
                                    extra_ingredient.extra_price = extra_ingredient.qty * extra_price;
                                }
                            }
                            if (qty_multiplier > 0 && basic_ingredient.qty === 0) {
                                // Means get back the default qty
                                basic_ingredient.qty = default_qty;
                                add_default_first = true;
                            }
                        }

                        var new_ingredients = [];
                        if (extra_ingredient) {
                            if (qty_multiplier === 0 && remove_extra) {
                                // Means NO qty. So, do direct amend original ingredient
                                extra_ingredient.qty = extra_ingredient.qty * qty_multiplier;
                                extra_ingredient.extra_price = extra_ingredient.qty * extra_price;
                            }

                            if (qty_multiplier > 0 && !add_default_first) {
                                // Means Extra/Half/Less qty of ingredient
                                // So, Need to add extra info inside ingredient
                                extra_ingredient.qty += qty * qty_multiplier;

                                // todo: Need to ask what price_multiplier do..
                                extra_ingredient.extra_price += qty * extra_price;

                                // `extra_ingredient.qty` can not exceed above `max_selection_qty`
                                extra_ingredient.times_added_extra += 1;
                                if (parseInt(extra_ingredient.times_added_extra) > parseInt(max_selection_qty)) {
                                    extra_ingredient.times_added_extra -= 1;
                                    extra_ingredient.qty -= qty * qty_multiplier;
                                    extra_ingredient.extra_price -= qty * extra_price;
                                }
                            }
                        } else {
                            if (qty_multiplier > 0 && !add_default_first) {
                                var new_line = {
                                    'id': product_id,
                                    'menu_id': orderline.get_product().id,
                                    'product_id': [product_id, product_name],
                                    'qty': qty,
                                    'extra_price': extra_price,
                                    'optional': false,
                                    'is_extra': true,
//                                    'special_extra': false,
                                    'recovery': recovery,
                                    'modifier_group_id': modifier_group_id,
                                    'times_added_extra': 1,
                                };
                                if (orderline.is_combo) {
                                    new_line.menu_id = orderline.active_menu_for_combo;
                                }
                                new_ingredients.push(new_line);
                            }
                        }

                        orderline.ingredients.push(new_ingredients);
                        orderline.ingredients = _.flatten(orderline.ingredients);

                        // Remove new_ingredients if it exceed above max_selection which is set inside Modifier Group
                        console.log("allow_multiple_selection>>>>>>>>>>>>>>>>>.", allow_multiple_selection, max_selection_qty, max_selection);
                        if (allow_multiple_selection) {
                            var count = _.countBy(orderline.ingredients, function(ing) {
                                return ing.is_extra && ing.modifier_group_id === modifier_group_id ? 'matched' : 'ignore'
                            });
                            if (count && count.matched > max_selection) {
                                // Remove object from `orderline.ingredients`
                                orderline.ingredients = _.without(orderline.ingredients,
                                    _.find(orderline.ingredients, {'is_extra': true, 'id': product_id}));
                            }
                        } else {
                            // @todo Not allowed Multiple Selection then it's like select another option
                            orderline.ingredients = _.without(orderline.ingredients,
                                    _.find(orderline.ingredients, {'is_extra': true, 'id': product_id}));
                        }

                        // Remove object from `orderline.ingredients` where `is_extra` is `true` and `qty` is `0`
                        orderline.ingredients = _.without(orderline.ingredients,
                            _.find(orderline.ingredients, {'is_extra': true, 'qty': 0}));

                        orderline.ingredients_show = _.filter(orderline.ingredients, function(ing) {
                            return ing.is_extra || (!ing.is_extra && ing.qty === 0) || ing.show_in_cart;
                        });

                        // set_unit_price for modified orderline
                        orderline.unmodified_price = orderline.product.get_price(orderline.order.pricelist, orderline.get_quantity());


                        // set_unit_price for modified orderline
                        orderline.modified_price = orderline.product.get_price(orderline.order.pricelist, orderline.get_quantity());
                        _.each(orderline.ingredients, function(ingredient) {
                            if (ingredient.extra_price) {
                                orderline.modified_price += ingredient.extra_price;
                            }
                        });

                        console.log("self.pos.get_order()>>>>>>>>>PRICE>>>>>>>.", orderline);

                    } else {
                        /**
                         *  If no opts active that means customer wants to swap the default ingredient
                         *  Combination of NO + EXTRA (For ex. NO - Whole Grain Bread & Add - Oatmeal Bread)
                         *
                         *  @todo Future Dev
                         *  For now it'll done in 2 steps..
                         *  Step 1: NO default ingredient
                         *  Step 2: ADD another ingredient from the same group
                         */
                    }
                } else {
                    // Special Modifier
                    console.log("Special Modifier>>>>>>>>>>>>>>>");
                    var id = $(ev).data('id'),
                        menu_id = $(ev).data('menu-id'),
                        menu_name = $(ev).data('menu-name');
                    console.log("menu_id>>>>>>>>>>>>>>>>>>", menu_id, orderline.special_modifiers_opts);
                    var current_opt = _.find(orderline.special_modifiers_opts, function(opt) {
                        return opt.id === id;
                    });
                    console.log("current_opt>>>>>>>>>>>>>>>>>", current_opt);
//                    if (_.contains(orderline.special_opts_lst, id)) {
//                        console.log("current_opt>>>>>>>need to remove>>>>>>>.", current_opt, orderline.special_opts_lst);
//                    } else {
                    var new_ingredients = [];
                    _.each(current_opt.modifier_products, function(mod_prod) {
                        // Consider as Extra/Modified Ingredient for Menu
                        var extra_ingredient = _.find(orderline.ingredients, function(line) {
                            return line.is_extra && line.id === mod_prod.product_id[0];
                        });
                        console.log("mod_prod>>>>>>>>>>>>>>>>>.", mod_prod, extra_ingredient);
                        if (extra_ingredient) {
                            if (mod_prod.qty_multiplier > 0 && !add_default_first) {
                                // Means Extra qty of ingredient
                                // So, Need to add extra info inside ingredient
                                extra_ingredient.qty = extra_ingredient.qty + mod_prod.qty;
                                extra_ingredient.extra_price = extra_ingredient.extra_price + mod_prod.extra_price;
                            }
                        } else {
                            var new_line = {
                                'id': mod_prod.product_id[0],
                                'menu_id': orderline.get_product().id,
                                'product_id': [mod_prod.product_id[0], mod_prod.product_id[1]],
                                'qty': mod_prod.qty,
                                'extra_price': mod_prod.extra_price,
                                'optional': false,
                                'is_extra': true,
                                'recovery': mod_prod.recovery,
                                'modifier_group_id': modifier_group_id,
                                'special_modifier_id': id,
                                'times_added_extra': 1,
                            };
                            new_ingredients.push(new_line);
                        }
                    });

                    orderline.ingredients.push(new_ingredients);
                    orderline.ingredients = _.flatten(orderline.ingredients);
                    orderline.special_opts_lst.push(id);

                    // Remove object from `orderline.ingredients` where `is_extra` is `true` and `qty` is `0`
                    orderline.ingredients = _.without(orderline.ingredients,
                        _.find(orderline.ingredients, {'is_extra': true, 'qty': 0}));

                    orderline.ingredients_show = _.filter(orderline.ingredients, function(ing) {
                        return ing.is_extra || (!ing.is_extra && ing.qty === 0) || ing.show_in_cart;
                    });

                    // set_unit_price for modified orderline
                    orderline.unmodified_price = orderline.product.get_price(orderline.order.pricelist, orderline.get_quantity());

                    // set_unit_price for modified orderline
                    orderline.modified_price = orderline.product.get_price(orderline.order.pricelist, orderline.get_quantity());
                    _.each(orderline.ingredients, function(ingredient) {
                        if (ingredient.extra_price) {
                            orderline.modified_price += ingredient.extra_price;
                        }
                    });

                    console.log("self.pos.get_order()>>>>>>>>>PRICE>>>>>>>.", orderline);
                }

                // Update the count badge for modifiers
                self.update_button_badge(ev, orderline);

                orderline.price_manually_set = true;
                orderline.modify_line = true;

                console.log("orderline>>>>FLATTEN>>>>>>>>>>>>.", orderline);

                // Currently pass the original value but already change the `get_unit_price` method
                // `set_unit_price` also trigger the change method which means re-render order
                orderline.set_unit_price(orderline.modified_price);
            }
        },

        click_to_select_combo: function(ev, orderline) {
            var self = this;
            console.log("click_to_select_combo>>>>>>>>>>>>", $(ev));
            var product_id = $(ev).data('menu-id');
            if (orderline.get_product().id !== product_id) {
                self.pos.get_order().remove_orderline(orderline);
                var product = self.pos.db.get_product_by_id(product_id);
                self.pos.get_order().add_product(product, {quantity: orderline.quantity});
            }
            return;
        },

        click_on_menu_list: function(ev, orderline) {
            var self = this;
            if (!$(ev).hasClass('product-option')) {
                console.log("click_on_menu_list>>>>>>>>>>>>", $(ev), $(ev).data('menu-id'), orderline);
                $(ev).parent().find('article.product').removeClass('menu-active');
                $(ev).addClass('menu-active');

                // Do the deep copy of orderline
                var copy_orderline = jQuery.extend(true, {}, orderline);

                copy_orderline.ingredients = _.filter(copy_orderline.ingredients, function(ingredient) {
                    return $(ev).data('menu-id') === ingredient.menu_id;
                });

                self.th_misc_details(copy_orderline, true);

                $('div.placeholder-ProductScreenWidget-Modifiers').empty();
                if (orderline.selected && orderline.quantity > 0) {
                    // Load modifiers & opts for active orderline
                    var el_str_m = $(QWeb.render('ProductScreenWidget-Modifiers', { widget: copy_orderline }));
                    var el_node_m = $('div.placeholder-ProductScreenWidget-Modifiers').html(el_str_m);
                    el_str_m.on('click', 'button.button,button.grp-special-opt-button', function() {
                        orderline.active_menu_for_combo = $(ev).data('menu-id');
                        self.click_on_modifier($(this), orderline);
                    });
                    el_str_m.on('click', 'button.grp-opt-button', function() {
                        self.click_on_modifier_opts($(this));
                    });

                    self.global_update_button_badge(copy_orderline);
                }
            } else {
                console.log("click_on_menu_list>>OPTION>>>>>>>>>>", $(ev), $(ev).data('menu-id'), orderline);
            }
        },

        click_on_smart_select: function(ev, orderline) {
            var self = this;
            console.log("click_on_smart_select>>>>>>>>>>>>>>", orderline);
            // Replace the active product with new one
            var product_id = $(ev).data('product-id');
            if (orderline.get_product().id !== product_id) {
                self.pos.get_order().remove_orderline(orderline);
                var product = self.pos.db.get_product_by_id(product_id);
                self.pos.get_order().add_product(product, {quantity: orderline.quantity});
            }
            return;
        },

        click_line: function(orderline, event) {
            var self = this;
            this._super(orderline, event);

            // Set top:0px & Empty the content for SmartSelect
            $('div.product-list-container').css({'top': '0px'});
            $('div.placeholder-SmartSelectWidget').empty();

            // Remove the class `menu-active-cart` from globally
            $('span.info-list-menus').removeClass('menu-active-cart');

            console.log("$(event.target)>>>>>>>>>>", $(event.target));
            if ($(event.target).hasClass('th-remove')) {
                console.log("Need to Remove Line...........", self, orderline.get_product());
                if (orderline.get_product().void_require_approval) {
                    // Open wizard to select manager & enter password
                    self.gui.select_user({
                        'security':       true,
                        'only_managers':  true,
                        'current_user':   false,
                        'title':          _t('Only managers can remove order-line!'),
                    }).then(function(user) {
                        self.pos.get_order().remove_orderline(orderline);
                    });
                } else {
                    self.pos.get_order().remove_orderline(orderline);
                }

                // Show product list again & empty the ComboListWidget
                $('div.placeholder-ComboListWidget').empty();
                $('div.product-list-container').removeClass('oe_hidden');
                return;
            } else if ($(event.target).hasClass('th-combo')) {
                console.log("Need to Make Combo............");
                // Set the ProductListWidget according to Combo
                $('div.product-list-container').addClass('oe_hidden');
                $('div.placeholder-ComboListWidget').empty();

                // Empty modifiers section
                $('div.placeholder-ProductScreenWidget-Modifiers').empty();

                // Load combo-menus
                var menu_lst = [];
                _.each(orderline.available_combos, function(menu) {
                    var menu = self.pos.db.get_product_by_id(menu.product_id[0]);
                    menu.image_url =  window.location.origin + '/web/image?model=product.product&field=image_medium&id='+ menu.id;
                    menu_lst.push(menu);
                });

                console.log("orderline.combo>>>>>>>>>>>>", orderline.available_combos);

                var el_str_combo = $(QWeb.render('ComboListWidget', {
                    widget: orderline,
                    menu_lst: menu_lst,
                    upsell_ids: [],
                }));
                var el_node_combo = $('div.placeholder-ComboListWidget').html(el_str_combo);
                el_str_combo.on('click', 'article.product', function() {
                    self.click_to_select_combo($(this), orderline);
                });

                return;
            } else if ($(event.target).hasClass('th-ala-carte')) {
                console.log("Need to Make A la Carte.......", orderline);

                var ala_carte_menu = _.find(orderline.menus, function(menu) {
                    return menu.default_menu_for_combo;
                });
                // Set the ComboListWidget empty
                $('div.product-list-container').removeClass('oe_hidden');
                $('div.placeholder-ComboListWidget').empty();

                // var product_id = $(ev).data('menu-id');
                if (orderline.get_product().id !== ala_carte_menu.product_id[0]) {
                    self.pos.get_order().remove_orderline(orderline);
                    var product = self.pos.db.get_product_by_id(ala_carte_menu.product_id[0]);
                    self.pos.get_order().add_product(product, {quantity: 1.0});
                }

                return;
            } else if ($(event.target).hasClass('th-combo-modify')) {
                console.log("Need to Modify Combo..........");
                // Set the ProductListWidget according to Combo
                $('div.product-list-container').addClass('oe_hidden');
                $('div.placeholder-ComboListWidget').empty();

                // Load menus for combo
                var menu_lst = [];
                var upsell_ids = [];
                _.each(orderline.menus, function(menu) {
                    console.log("menu>>>>>>>>>>>>>>>>", menu);
                    var prod = self.pos.db.get_product_by_id(menu.product_id[0]);
                    prod.image_url =  window.location.origin + '/web/image?model=product.product&field=image_medium&id='+ menu.id;
                    menu_lst.push(prod);

                    upsell_ids.push({
                        'menu_id': menu.product_id[0],
                        'menu_name': menu.product_id[1],
                        'menu_upsell_ids': menu.menu_upsell_ids,
                        'menu_upsell_lines': false,
                        'menu_upsell_list': false,
                    });
                });

                _.each(upsell_ids, function(upsell_id) {
                    upsell_id.menu_upsell_lines = _.filter(self.pos.all_menus_for_upsell, function(menu_upsell) {
                        return _.contains(upsell_id.menu_upsell_ids, menu_upsell.id);
                    });
                    console.log("upsell_id>>>>>>>>>>>>>>>>", upsell_id);
                    var opt_menu_lst = [];

                    _.each(upsell_id.menu_upsell_lines, function(line) {
                        var categ = line.pos_categ_id[0];
                        var categ_prods = self.pos.db.get_product_by_category(categ);
                        console.log("categ_prods>>>>>>>>>>>>>>>>>", categ, categ_prods, opt_menu_lst);
                        console.log("categ>>>>>>>>>>>>>>", opt_menu_lst, categ_prods, opt_menu_lst.concat(categ_prods));
                        opt_menu_lst = opt_menu_lst.concat(categ_prods);
                    });
                    _.each(opt_menu_lst, function(menu) {
                        menu.image_url =  window.location.origin + '/web/image?model=product.product&field=image_medium&id='+ menu.id;
                    });
                    console.log("opt_menu_lst>>>>>>>>>>>>>>>.", opt_menu_lst);
                    upsell_id.menu_upsell_list = opt_menu_lst;
                });

                console.log("menu_lst>>>>>>>>>>>>>>>>>>.", menu_lst, upsell_ids, orderline, self.pos.all_menus_for_upsell);
                var el_str_combo = $(QWeb.render('ComboListWidget', {
                    widget: orderline,
                    menu_lst: menu_lst,
                    upsell_ids: upsell_ids,
                }));
                var el_node_combo = $('div.placeholder-ComboListWidget').html(el_str_combo);
                el_str_combo.on('click', 'article.product', function() {
                    self.click_on_menu_list($(this), orderline);
                });

                return;
            } else {
                console.log("Re-select line again..........", orderline);
                // Show product list again & empty the ComboListWidget
                $('div.placeholder-ComboListWidget').empty();
                $('div.product-list-container').removeClass('oe_hidden');

                $('div.placeholder-ProductScreenWidget-Modifiers').empty();
                if (orderline.selected && orderline.quantity > 0 && !orderline.get_product().is_menu_combo) {
                    // Load modifiers & opts for active orderline
                    self.load_modifiers_opts(orderline);

                    // Update the count badge for modifiers
                    self.global_update_button_badge(orderline);

                }

                // Load Smart Selection for active orderline
                self.load_smart_selection(orderline);
            }
        },

        render_orderline: function(orderline) {
            var self = this;

            /*
             *  Adds Ingredients & Modifiers info in orderline
             *
             *  FIXME should be moved elsewhere...
             *  Move this block of code under ``models.Orderline``,
             *  using set & get method...
             */
            // ================ START ================
            if (!orderline.modify_line) {
                var all_menu_for_combo = _.filter(self.pos.all_menus_for_combo, function(menu) {
                    return _.contains(orderline.get_product().combo_menu_ids, menu.id);
                });

                orderline.menus = _.map(all_menu_for_combo, _.clone);

                orderline.menus = _.sortBy(orderline.menus, function(menu) {
                    return menu.sequence;
                });

                if (orderline.get_product().is_menu_combo) {
                    var all_ingredients = [];
                    var product_lst = [];
                    _.each(orderline.menus, function(menu) {
                        var product = self.pos.db.get_product_by_id(menu.product_id[0]);
                        product_lst.push(menu.product_id[0]);
                        _.filter(self.pos.all_ingredients, function(ingredient) {
                            if (_.contains(product.product_ingredient_ids, ingredient.id)) {
                                ingredient.menu_id = menu.product_id[0];
                                all_ingredients.push(ingredient);
                            }
                        });
                    });
                    orderline.is_combo = true;
                } else {
                    orderline.is_combo = false;

                    var current_order = self.pos.get_order();
                    var current_pricelist = self.pos.default_pricelist;

                    if (current_order) {
                        current_pricelist = current_order.pricelist;
                    }

                    orderline.available_combos = _.filter(current_pricelist.items, function(item){
                        return _.contains(orderline.get_product().primary_menu_in_combo_ids, item.product_id[0])
                    });

                    var all_ingredients = _.filter(self.pos.all_ingredients, function(ingredient) {
                        return _.contains(orderline.get_product().product_ingredient_ids, ingredient.id);
                    });
                }

                /**
                 *  Need to clone of all_ingredients & then assign to orderline.ingredients
                 *  Otherwise JS will redirect to same reference as
                 *  its just a different name to access/modify same list of objects
                 *
                 *  So, Need to create a new array of object which have its own reference
                 *
                 *  Can also use plain vanilla way using `JSON.parse` but it have its own disadvantages
                 *  - performance is bad & its only work when we've JSON-serializable content
                 *
                 *  For ex.
                 *  orderline.ingredients = JSON.parse(JSON.stringify(all_ingredients));
                 *
                 */
                orderline.ingredients = _.map(all_ingredients, _.clone);

                self.th_misc_details(orderline, false);
            }
            // ================ END ================

            var el_str  = QWeb.render('Orderline',{widget:this, line:orderline});
            var el_node = document.createElement('div');
                el_node.innerHTML = _.str.trim(el_str);
                el_node = el_node.childNodes[0];
                el_node.orderline = orderline;
                el_node.addEventListener('click',this.line_click_handler);
            var el_lot_icon = el_node.querySelector('.line-lot-icon');
            if(el_lot_icon){
                el_lot_icon.addEventListener('click', (function() {
                    this.show_product_lot(orderline);
                }.bind(this)));
            }
            orderline.node = el_node;

            // Show Combo & Ala Carte button in active orderline
            if (orderline.selected) {
                if (orderline.get_product().is_menu_combo) {
                    $(el_node).find('.button.th-ala-carte').removeClass('oe_hidden');
                    $(el_node).find('.button.th-combo-modify').removeClass('oe_hidden');
                } else {
                    console.log("orderline.available_combos>>>>>>>>>>>>>>>>>", orderline.available_combos);
                    if (orderline.available_combos.length > 0) {
                        $(el_node).find('.button.th-combo').removeClass('oe_hidden');
                    }
                }
            }

            if (!orderline.modify_line && !orderline.get_product().is_menu_combo) {
                // Load modifiers & opts for active orderline
                self.load_modifiers_opts(orderline);
            }


            // Load smart select widget for active ordeline
            self.load_smart_selection(orderline);

            if (orderline.modify_line && orderline.get_product().is_menu_combo && $('div.modify-combo-section').length !== 0) {
                $('div.product-list-container').addClass('oe_hidden');
            } else {
                if (orderline.get_product().is_menu_combo) {
                    // Empty the modifier & combo list widget space if any
                    $('div.placeholder-ProductScreenWidget-Modifiers').empty();
                    $('div.placeholder-ComboListWidget').empty();
                    $('div.product-list-container').removeClass('oe_hidden');
                }
            }
            console.log("orderline>>>>>>>>>>>>>>", orderline);
            return el_node;
        },

        remove_orderline: function(order_line){
            this._super(order_line);
            // Empty modifier space
            $('div.placeholder-ProductScreenWidget-Modifiers').empty();
        },

        update_summary: function(){
            this._super();

            // Need to set original price again, if accidentally refresh the page
            var order = this.pos.get_order();
            _.each(order.get_orderlines(), function(line) {
                var original_price = line.product.get_price(line.order.pricelist, line.get_quantity());
                if (line.price !== original_price && !line.modify_line) {
                    line.set_unit_price(original_price);
                }
            });
        },
    });

    screens.ProductScreenWidget.include({
        start: function() {
            var self = this;
            this._super();
            PRODUCT_CATEGORIES_WIDGET = this.product_categories_widget;

            // Global function which check menu list every 30 Seconds
            setInterval(function() {
                self.globally_check_menu_lst();
            }, 30000);
        },
        globally_check_menu_lst: function() {
            console.log("Globally>>>>>>>>>>>");

            var smart_select = false;
            if ($('div.smart-select-buttons').length !== 0) {
                var smart_select = true;
            }

            var combo_screen = false;
            if ($('div.modify-combo-section').length !== 0) {
                var combo_screen = true;
            }

            // Render the product list according to current active category
            PRODUCT_CATEGORIES_WIDGET.renderElement(smart_select, combo_screen);

        },
    });

    // Load menus according to pricelist when customer is changed
    screens.ClientListScreenWidget.include({
        save_changes: function() {
            var self = this;
            this._super();

            // Empty the smart select space if any
            $('div.product-list-container').css({'top': '0px'});
            $('div.placeholder-SmartSelectWidget').empty();

            // Render the product list according to current active category
            PRODUCT_CATEGORIES_WIDGET.renderElement();

            // Render Top Selling Section...
            TOP_SELLING_MENUS_WIDGET.renderElement();
        },
    });

    // Load menus according to pricelist when pricelist is changed
    screens.set_pricelist_button.include({
        button_click: function () {
            var self = this;

            var pricelists = _.map(self.pos.pricelists, function (pricelist) {
                return {
                    label: pricelist.name,
                    item: pricelist
                };
            });

            self.gui.show_popup('selection',{
                title: _t('Select pricelist'),
                list: pricelists,
                confirm: function (pricelist) {
                    var order = self.pos.get_order();
                    order.set_pricelist(pricelist);

                    // Empty the smart select space if any
                    $('div.product-list-container').css({'top': '0px'});
                    $('div.placeholder-SmartSelectWidget').empty();

                    // Render the product list according to current active category
                    PRODUCT_CATEGORIES_WIDGET.renderElement();

                    // Render Top Selling Section...
                    TOP_SELLING_MENUS_WIDGET.renderElement();

                    // Bad Hack for dummy pricelist button label
                    $('button.o_pricelist_button_dummy').text(pricelist.display_name);
                },
                is_selected: function (pricelist) {
                    return pricelist.id === self.pos.get_order().pricelist.id;
                }
            });
        },
    });

    screens.ReceiptScreenWidget.include({
        click_next: function() {
            this._super();
            // On next order clean the modifier space
            $('div.placeholder-ProductScreenWidget-Modifiers').empty();

            // Empty the smart select space if any
            $('div.product-list-container').css({'top': '0px'});
            $('div.placeholder-SmartSelectWidget').empty();
        },
    });

});
