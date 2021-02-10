odoo.define('th_point_of_sale.chrome', function (require) {
    "use strict";

    var chrome = require('point_of_sale.chrome');
    var gui = require('point_of_sale.gui');

    chrome.OrderSelectorWidget.include({
        deleteorder_click_handler: function(event, $el) {
            var self = this;
            var order = this.pos.get_order();
            if (!order) {
                return;
            } else if ( !order.is_empty() ){
                this.gui.show_popup('confirm',{
                    'title': _t('Destroy Current Order ?'),
                    'body': _t('You will lose any data associated with the current order'),
                    confirm: function(){
                        // Open wizard to select manager & enter password
                        self.gui.select_user({
                            'security':       true,
                            'only_managers':  true,
                            'current_user':   false,
                            'title':          _t('Only managers can remove whole order!'),
                        }).then(function(user) {
                            self.pos.delete_current_order();
                        });
                    },
                });
            } else {
                this.pos.delete_current_order();
            }
        }
    });

});
