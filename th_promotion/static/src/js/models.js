odoo.define('th_promotion.models', function (require) {
    "use strict";

    var core = require('web.core');
    var models = require('point_of_sale.models');
    var utils = require('web.utils');
    var Backbone = window['Backbone'];

    // Load: Menu Category
    models.load_models({
        model: 'th.promotion',
        fields: [],
        domain: ['|', ['end_date', '>=', moment().format("YYYY-MM-DD")], ['end_date', '=', false]],
        loaded: function(self, promotions) {
            let _promotions = {};
            promotions.map((data) => _promotions[data.id] = data);
            self.promotions = _promotions;
            self.db.promotions = _promotions;
        },
    });

    models.load_models({
        model: 'th.promotion.rule',
        fields: [],
        loaded: function(self, promotion_rules) {
            let _rules = {};
            promotion_rules.map((data) => _rules[data.id] = data);
            self.promotion_rules = _rules;
            self.db.promotion_rules = _rules;
        },
    });

    models.Promotion = Backbone.Model.extend({
        initialize: function(attr, options){
            this.pos   = options.pos;
            this.promotionsByType = this.preparePromotion();
            this.promotionByProductId = this.preparePromotionByProduct();
        },
        passCondition: function () {
            return true;
        },
        checkCondition: function (domain, data) {
            let condition = domain[1], value = domain[2], result = false;
            switch (condition) {
                case "like":
                    result = data.includes(value);
                    break;
                case "iLike":
                    result = data.includes(value.toLocaleLowerCase());
                    break;
                case "=":
                    result = data === value;
                    break;
                case "!=":
                    result = data !== value;
                    break;
                default:
                    result = false;
                    break;
            }
            return result;
        },
        checkDomain: function (domain, data) {
            let result = true;
            for (let i=0; i<domain.length; i++) {
                let _domain = domain[i], _data = data[_domain[0]];
                if (!_data || !this.checkCondition(domain[i], _data)) {
                    result = false;
                    break;
                }
            }
            return result;
        },
        searchPromotion: function (domain) {

        },
        searchRule: function (domain) {

        },
        searchProduct: function (domain) {
            const product_by_id = this.pos.db.product_by_id;
            let result = [];
            Object['values'](product_by_id).map((product) => {
                if (this.checkDomain(domain, product)) {
                    result.push(product);
                }
            });
            return result;
        },
        groupProductByOrder: function () {
            let productGroup = {};
            const orderLines = this.pos.get_order().orderlines.models;
            orderLines.map((line) => {
                const product = line.product;
                if (!productGroup.hasOwnProperty(product.id)) {
                    productGroup[product.id] = {qty: 0, price: 0, lines: []};
                }
                productGroup[product.id].qty += line.qty;
                productGroup[product.id].price += line.price;
                productGroup[product.id].lines.push(line);
            });
            return productGroup;
        },
        preparePromotionOrder: function () {
            let self = this;
            let promotionsResult = {};
            const productGroup = this.groupProductByOrder();
            Object['keys'](productGroup).map((productID) => {
                const product = productGroup[productID],
                    productPromotion = self.promotionByProductId[productID];
                if (productPromotion && productPromotion.promotions) {
                    const {promotions} = productPromotion;
                    Object['keys'](promotions).map((promotionID) => {
                        const promotion = promotions[promotionID], {obj, rules} = promotion;
                        // let newRules = {available: {}, unavailable: {}};
                        let newRules = {};
                        Object['keys'](rules).map((ruleID) => {
                            const rule = rules[ruleID];
                            // self.passCondition() ? newRules.available[ruleID] = rule : newRules.unavailable[ruleID] = rule;
                            newRules[ruleID] = rule;
                        });
                        promotionsResult[promotionID] = {obj: obj, rules: newRules};
                    });
                }
            });
            return promotionsResult;
        },
        preparePromotion: function () {
            const {promotions, promotion_rules} = this.pos;
            let promotionsResult = {};
            Object['keys'](promotions).map((promotionId) => {
                const promotion = promotions[promotionId], {promotion_rule_ids} = promotion;
                let rules = {};
                promotion_rule_ids.map((ruleId) => {
                    rules[ruleId] = promotion_rules[ruleId];
                });
                promotionsResult[promotionId] = {obj: promotion, rules: rules};
            });
            return promotionsResult;
        },
        getExApProduct: function (rule) {
            let getProductByCate = (cateId) => this.pos.db.get_product_by_category(cateId).map((product) => product.id);
            const {apply_menu_ids, apply_category_ids, exclude_category_ids, exclude_menu_ids} = rule
            let excludeProduct = exclude_menu_ids, applyProduct = apply_menu_ids;
            if (apply_category_ids.length > 0) {
                apply_category_ids.map((cateId) => {
                    applyProduct = getProductByCate(cateId);
                });
            }
            if (exclude_category_ids.length > 0) {
                exclude_category_ids.map((cateId) => {
                    excludeProduct = getProductByCate(cateId);
                });
            }
            return {excludeProduct: excludeProduct, applyProduct: applyProduct}
        },
        preparePromotionByProduct: function () {
            let self = this;
            let promotionByProduct = {};
            Object['keys'](self.promotionsByType).map((promotionId) => {
                const promotion = self.promotionsByType[promotionId], {rules} = promotion;
                Object['keys'](rules).map((ruleId) => {
                    const rule = rules[ruleId], {applyProduct, excludeProduct} = self.getExApProduct(rule);
                    applyProduct.map((productID) => {
                        if (!excludeProduct.includes(productID)) {
                            if (!promotionByProduct.hasOwnProperty(productID)) {
                                promotionByProduct[productID] = {promotions: {}};
                            }
                            if (!promotionByProduct[productID].hasOwnProperty(promotionId)) {
                                promotionByProduct[productID].promotions[promotionId] = {obj: promotion.obj, rules: {}};
                            }
                            promotionByProduct[productID].promotions[promotionId].rules[ruleId] = rule;
                        }
                    })
                })
            });
            return promotionByProduct;
        },
    });
});
