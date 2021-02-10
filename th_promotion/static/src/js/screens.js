odoo.define('th_promotion.screens', function (require) {
    "use strict";

    var core = require('web.core');
    var PosBaseWidget = require('point_of_sale.BaseWidget');
    var screens = require('point_of_sale.screens');

    var QWeb = core.qweb;
    var _t = core._t;


    screens.ActionpadWidget.include({
        onClickDiscount: function () {
            let {products, promotions_screen} = this.gui.screen_instances, params = {};
            products.$el.find(".pads-bottom").append($(`<div class="placeholder-OrderWidget">`));
            promotions_screen.setOrderWidget(products.order_widget);
            const {promotion} = this.pos.modelInstance;
            if (promotions_screen.getStackLength() <= 1) {
                params = {promotions: promotion.preparePromotionOrder(), screensInstance: this.gui.screen_instances};
            }
            this.gui.show_screen('promotions_screen', params);
        },
        renderElement: function() {
            var self = this;
            this._super();

            this.$('.btnViewDiscount').click(() => {
                self.onClickDiscount();
            });
        },
    });

    screens.ProductScreenWidget.include({
        start: function() {
            this._super();
        },
        setOrderWidget: function (orderWidget) {
            let target = this.$el.find('.placeholder-OrderWidget')[0];
            target.parentNode.replaceChild(orderWidget.el, target);
            this.order_widget = orderWidget;
        },
        showPromotionPopup: function (product) {
            const {promotion} = this.pos.modelInstance;
            let productPromotion = promotion.promotionByProductId[product.id];
            if (productPromotion) {
                this.gui.show_popup('promotion_popup', {promotions: productPromotion.promotions});
            }
        },
        click_product: function(product) {
            this._super(product);
            this.showPromotionPopup(product);
        },
    });
});
