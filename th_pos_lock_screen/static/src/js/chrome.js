odoo.define('th_pos_lock_screen.chrome', function(require) {
    "use strict";

    var PosBaseWidget = require('point_of_sale.BaseWidget');
    var gui = require('point_of_sale.gui');
    var Chrome = require('point_of_sale.chrome');
    var core = require('web.core');

    var _t = core._t;

    var idleTime = 0;

    function idealScreenCheck(gui, pos) {
        var auto_lock_time_minute = pos.config.auto_lock_time;
        var auto_lock_time = auto_lock_time_minute * 60;  // In Seconds
        var idleInterval = setInterval(function() {
            if (gui.is_screen_lock) {
                clearInterval(idleInterval);
            }
            idleTime = idleTime + 1;
            if (idleTime == auto_lock_time) {
                clearInterval(idleInterval);

                /**
                 *  Active parameter `is_screen_lock` to
                 *  mark active screen as locked screen.
                 */
                gui.is_screen_lock = true;

                gui.select_user({
                    'security':     true,
                    'current_user': false,
                    'title':        _t('Screen is locked! Please, Select cashier.'),
                }).then(function(user) {
                    pos.set_cashier(user);

                    var UsernameWidgetProto = new Chrome.UsernameWidget();
                    /**
                     *  @todo Siddharth Bhalgami
                     *  Change the __proto__ can be dangerous sometimes...
                     *  Need to check for the better & safer way to
                     *  achieve the same feature
                     */
                    UsernameWidgetProto.$el = $(document).find('span.username');
                    UsernameWidgetProto.el = $(document).find('span.username')[0];
                    UsernameWidgetProto.gui = gui;
                    UsernameWidgetProto.pos = pos;

                    var UsernameWidgetRenderElement = Chrome.UsernameWidget.prototype.renderElement.bind(UsernameWidgetProto);
                    UsernameWidgetRenderElement();
                });
            }
        }, 1000); // Check for every second

        // Zero the idle timer on multiple events.
        $(document).on('click touch keydown mousemove', function(event) {
            idleTime = 0;
        });
    };

    var LockScreenButtonWidget = PosBaseWidget.extend({
        template: 'LockScreenButtonWidget',

        init: function(parent, options) {
            options = options || {};
            this._super(parent, options);
        },

        renderElement: function() {
            var self = this;
            this._super();
            if (self.pos.config.auto_lock_time > 0) {
                self.afterScreenUnlock(self.gui, self.pos);
            }
            this.$('.js_lock_screen').click(function(e) {
                self.gui.show_popup('lock_screen');
            });
        },

        afterScreenUnlock: function(gui, pos) {
            var self = this;
            if (!gui.is_screen_lock) {
                idealScreenCheck(gui, pos);
            }
        },

    });

    Chrome.Chrome.prototype.widgets.push({
        'name':   'lock_screen_button',
        'widget': LockScreenButtonWidget,
        'append':  '.pos-rightheader',
    });

    return {
        LockScreenButtonWidget: LockScreenButtonWidget,
    };

});
