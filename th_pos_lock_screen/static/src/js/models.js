odoo.define('th_pos_lock_screen.models', function (require) {
    "use strict";

    var models = require('point_of_sale.models');
    var core = require('web.core');

    models.load_fields("pos.config", ['outlet_id']);

    // Load: Outlet
    models.load_models({
        model: 'stock.warehouse',
        fields: [],
        loaded: function(self, all_outlet){
            self.all_outlet = _.filter(all_outlet, function(outlet) {
                return outlet.is_outlet;
            });
        },
    });

});
