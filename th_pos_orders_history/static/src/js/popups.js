odoo.define('th_pos_orders_history.popups', function(require) {
    "use strict";

    var PopupWidget = require('th_point_of_sale.popups');
    var screens = require('point_of_sale.screens');

    PopupWidget.FunctionsPopupWidget.include({
        init: function(parent, args) {
            var self = this;
            this._super(parent, args);

            // Re-init OrderHistory widget
            this.widget_order_history = new screens.OrdersHistoryButton(self, {});
        },

        events: _.extend({}, PopupWidget.FunctionsPopupWidget.prototype.events, {
            'click .button.order-history':  'click_order_history',
        }),

        click_order_history: function(ev) {
            this.widget_order_history.button_click();
        },
    });

});
