odoo.define('th_pos_lock_screen.gui', function(require) {
    "use strict";

    var core = require('web.core');
    var gui = require('point_of_sale.gui');
    var Chrome = require('point_of_sale.chrome');
    var thChrome = require('th_pos_lock_screen.chrome');

    var _t  = core._t;

    gui.Gui.include({
        init: function(options) {
            var self = this;
            this._super(options);

            // Locked screen from start
            this.is_screen_lock = true;

            // Keep POS screen locked while load/reload
            this.chrome.ready.then(function() {
                self.select_user({
                    'security':     true,
                    'current_user': false,
                    'title':        _t('Please, Select cashier.'),
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
                    UsernameWidgetProto.gui = self;
                    UsernameWidgetProto.pos = self.pos;
                    UsernameWidgetProto.chrome = self.chrome;

                    var UsernameWidgetRenderElement = Chrome.UsernameWidget.prototype.renderElement.bind(UsernameWidgetProto);
                    UsernameWidgetRenderElement();
                });
            });
        },

        // A Generic UI that allow to select a user from a list.
        // It returns a deferred that resolves with the selected user
        // upon success. Several options are available :
        // - security: passwords will be asked
        // - only_managers: restricts the list to managers
        // - current_user: password will not be asked if this
        //                 user is selected.
        // - title: The title of the user selection list.
        select_user: function(options){
            options = options || {};
            var self = this;
            var def  = new $.Deferred();
            var active_outlet = _.find(this.pos.all_outlet, function(outlet) {
                return self.pos.config.outlet_id[0] === outlet.id;
            });
            var users = active_outlet.users,
                managers = active_outlet.store_managers;

            var list = [];
            for (var i = 0; i < this.pos.users.length; i++) {
                var user = this.pos.users[i];
                // Load only managers
                if (_.contains(managers, user.id)) {
                    if (!options.only_managers || user.role === 'manager') {
                        list.push({
                            'label': user.name,
                            'item':  user,
                        });
                    }
                }
            }
            // Load the current user
            var already_in = _.find(list, function(rec) {
                return rec.item.id === self.pos.user.id;
            });
            if (!already_in && !options.only_managers) {
                list.push({
                    'label': self.pos.user.name,
                    'item': self.pos.user,
                })
            }

            this.show_popup('selection',{
                title: options.title || _t('Select User'),
                list: list,
                confirm: function(user){ def.resolve(user); },
                cancel: function(){ def.reject(); },
                is_selected: function(user){ return user === self.pos.get_cashier(); },
            });

            return def.then(function(user){
                if (options.security && user !== options.current_user && user.pos_security_pin) {
                    return self.ask_password(user.pos_security_pin).then(function(){
                        return user;
                    });
                } else {
                    return user;
                }
            });
        },

        // Ask for a password, and checks if it this
        // the same as specified by the function call.
        // returns a deferred that resolves on success,
        // fails on failure.
        ask_password: function(password) {
            var self = this;
            var ret = new $.Deferred();
            if (password) {
                var title = 'Password ?';
                self.lock_loop(password, ret, title);
            } else {
                ret.resolve();
                /**
                 *  Release parameter `is_screen_lock` to
                 *  mark active screen as unlocked screen.
                 */
                self.is_screen_lock = false;

                // Re-check the auto screen lock mechanism
                thChrome.LockScreenButtonWidget.prototype.afterScreenUnlock(self, self.pos);
            }
            return ret;
        },

        // Recursive function
        // Which ask password again if given password is incorrect.
        lock_loop: function(password, ret, title) {
            var self = this;
            self.show_popup('password',{
                'title': _t(title),
                confirm: function(pw) {
                    if (pw !== password) {
                        var title = 'Incorrect! Try again...';
                        self.lock_loop(password, ret, title);
    //                    self.show_popup('error',_t('Incorrect Password'));
    //                    ret.reject();
                    } else {
                        ret.resolve();
                        /**
                         *  Release parameter `is_screen_lock` to
                         *  mark active screen as unlocked screen.
                         */
                        self.is_screen_lock = false;

                        // Re-check the auto screen lock mechanism
                        thChrome.LockScreenButtonWidget.prototype.afterScreenUnlock(self, self.pos);
                    }
                },
            });
        },
    });

});
