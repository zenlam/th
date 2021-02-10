odoo.define('th_promotion.popups', function(require) {
    "use strict";

    var PopupWidget = require('point_of_sale.popups');
    var gui = require('point_of_sale.gui');
    var screens = require('point_of_sale.screens');
    var models = require('point_of_sale.models');
    var Chrome = require('point_of_sale.chrome');
    var promotion = require('th_promotion.promotion')
    var core = require('web.core');

    var _t  = core._t;

    var PromotionPopupWidget = PopupWidget.extend({
        template: 'PromotionPopupWidget',

        init: function(parent, args) {
            this._super(parent, args);
        },
        show: function(options){
            this.promotions = options.promotions || this.pos.promotionsByType;
            this.renderElement();
        },
        onClickPromotion: function (promotion) {
        },
        renderPromotion: function () {
            this.promotionView = new promotion.PromotionScreenWidget(this,
                {promotions: this.promotions, group: false});
            this.promotionView.renderElement();
            this.$el.find('.body').append(this.promotionView.$el);
        },
        bindAction: function () {
        },
        renderElement: function() {
            this._super();
            this.renderPromotion();
            this.bindAction();
        },
    });

    gui.define_popup({name:'promotion_popup', widget: PromotionPopupWidget});

    return {
        PromotionPopupWidget: PromotionPopupWidget,
    };

});
