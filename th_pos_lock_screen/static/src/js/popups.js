odoo.define('th_pos_lock_screen.popups', function(require) {
    "use strict";

    var PopupWidget = require('point_of_sale.popups');
    var gui = require('point_of_sale.gui');
    var Chrome = require('point_of_sale.chrome');
    var core = require('web.core');

    var _t  = core._t;

    var selectionPopUp = _.find(gui.Gui.prototype.popup_classes, function(popup_class) { return popup_class.name == 'selection' });
    var passwordPopUp = _.find(gui.Gui.prototype.popup_classes, function(popup_class) { return popup_class.name == 'password' });

    selectionPopUp.widget.include({
        show: function(options) {
            var self = this;
            this._super(options);

            /**
             *  If screen is locked, remove cancel button from PopUp
             */
            if (self.gui.is_screen_lock) {
                $(self.$el).find('.popup-selection .button.cancel').addClass('oe_hidden');
            } else {
                $(self.$el).find('.popup-selection .button.cancel').removeClass('oe_hidden');
            }
        },
    });

    passwordPopUp.widget.include({
        click_cancel: function() {
            var self = this;
            /**
             *  If screen is lock, change the cancel button mechanism
             *
             *  true   :  Open the Select Cashier screen again
             *  false  :  Close the password popup
             */
            if (self.gui.is_screen_lock) {
                self.gui.select_user({
                    'security':     true,
                    'current_user': false,
                    'title':        _t('Screen is locked! Please, Select cashier.'),
                }).then(function(user) {
                    self.pos.set_cashier(user);

                    var UsernameWidgetProto = new Chrome.UsernameWidget();
                    /**
                     *  @todo Siddharth Bhalgami
                     *  Change the __proto__ can be dangerous sometimes...
                     *  Need to check for the better & safer way to
                     *  achieve the same feature
                     */
                    UsernameWidgetProto.$el = $(document).find('span.username');
                    UsernameWidgetProto.el = $(document).find('span.username')[0];
                    UsernameWidgetProto.gui = self.gui;
                    UsernameWidgetProto.pos = self.pos;

                    var UsernameWidgetRenderElement = Chrome.UsernameWidget.prototype.renderElement.bind(UsernameWidgetProto);
                    UsernameWidgetRenderElement();
                });
            } else {
                self._super();
            }
        },
    });

    var LockScreenPopupWidget = PopupWidget.extend({
        template: 'LockScreenPopupWidget',
        show: function(options) {
            var self = this;
            options = options || {};
            this._super(options);
            this.renderElement();
            $('div.confirm-lock').on('click', function() {
                /**
                 *  Active parameter `is_screen_lock` to
                 *  mark active screen as locked screen.
                 */
                self.gui.is_screen_lock = true;

                self.gui.select_user({
                    'security':     true,
                    'current_user': false,
                    'title':        _t('Screen is locked! Please, Select cashier.'),
                }).then(function(user) {
                    self.pos.set_cashier(user);

                    var UsernameWidgetProto = new Chrome.UsernameWidget();
                    /**
                     *  @todo Siddharth Bhalgami
                     *  Change the __proto__ can be dangerous...
                     *  Need to check for the better & safe way to
                     *  achieve the same feature
                     */
                    UsernameWidgetProto.$el = $(document).find('span.username');
                    UsernameWidgetProto.el = $(document).find('span.username')[0];
                    UsernameWidgetProto.gui = self.gui;
                    UsernameWidgetProto.pos = self.pos;

                    var UsernameWidgetRenderElement = Chrome.UsernameWidget.prototype.renderElement.bind(UsernameWidgetProto);
                    UsernameWidgetRenderElement();
                });
            });
        },
    });
    gui.define_popup({name:'lock_screen', widget: LockScreenPopupWidget});

    return {
        LockScreenPopupWidget: LockScreenPopupWidget,
    };

});
