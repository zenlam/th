odoo.define('th_pos_orderline_note.notes', function (require) {
    "use strict";

    var models = require('point_of_sale.models');
    var screens = require('point_of_sale.screens');
    var gui = require('point_of_sale.gui');
    var core = require('web.core');
    var PopupWidget = require('point_of_sale.popups');

    var QWeb = core.qweb;
    var _t   = core._t;

    // Part of Onnet Consulting Sdn Bhd
    models.load_models({
        model: 'th.orderline.note',
        fields: ['id', 'sequence', 'name'],
        loaded: function(self, all_orderline_notes) {
            self.all_orderline_notes = all_orderline_notes;
        },
    });

    // Part of Odoo S.A.
    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function(attr, options) {
            _super_orderline.initialize.call(this,attr,options);
            this.note = this.note || "";
        },
        set_note: function(note){
            this.note = note;
            this.trigger('change',this);
        },
        get_note: function(note){
            return this.note;
        },
        can_be_merged_with: function(orderline) {
            if (orderline.get_note() !== this.get_note()) {
                return false;
            } else {
                return _super_orderline.can_be_merged_with.apply(this,arguments);
            }
        },
        clone: function(){
            var orderline = _super_orderline.clone.call(this);
            orderline.note = this.note;
            return orderline;
        },
        export_as_JSON: function(){
            var json = _super_orderline.export_as_JSON.call(this);
            json.note = this.note;
            return json;
        },
        // @todo Siddharth Bhalgami
        //      Later Need to check...
        //      For now Remove the Note on Reload the POS Screen
        // init_from_JSON: function(json){
        //     _super_orderline.init_from_JSON.apply(this,arguments);
        //     this.note = json.note;
        // },
    });

    // Part of Onnet Consulting Sdn Bhd
    var OrderlineNotesPopupWidget = PopupWidget.extend({
        template: 'OrderlineNotesPopupWidget',
        events: _.extend({}, PopupWidget.prototype.events, {
            'click .button.quick-note':  'click_quick_note',
        }),

        click_quick_note: function (ev) {
            var $textArea = $('textarea.note-area');
            if ($textArea.val()) {
                var note = $textArea.val() + ' ' + $(ev.target).data('note');
                $textArea.val(note);
            } else {
                var note = $(ev.target).data('note');
                $textArea.val(note);
            }
        },

        click_confirm: function(){
            var value = this.$('input,textarea').val();
            this.gui.close_popup();
            if( this.options.confirm ){
                this.options.confirm.call(this,value);
            }
        },
    });
    gui.define_popup({name:'orderline_notes', widget: OrderlineNotesPopupWidget});

    // Part of Odoo S.A.
    var OrderlineNoteButton = screens.ActionButtonWidget.extend({
        template: 'OrderlineNoteButton',
        button_click: function(){
            var line = this.pos.get_order().get_selected_orderline();
            if (line) {
                this.gui.show_popup('orderline_notes',{
                    title: _t('Add Note'),
                    value:   line.get_note(),
                    confirm: function(note) {
                        line.set_note(note);
                    },
                });
            }
        },
    });

    // Part of Onnet Consulting Sdn Bhd
    screens.OrderWidget.include({
        init: function(parent, options) {
            var self = this;
            this._super(parent, options);

            // Init OrderlineNoteButton widget
            this.widget_orderlinenotebutton = new OrderlineNoteButton(self, {});
        },

        click_on_modifier: function(ev, orderline) {
            var self = this;
            var id = $(ev).data('id'),
                name = $(ev).data('name');

            if(id === 'note' && name === 'note') {
                // Call the OrderlineNoteButton widget
                self.widget_orderlinenotebutton.button_click();
            } else {
                this._super(ev, orderline);
            }
        }
    });

    return {
        OrderlineNotesPopupWidget: OrderlineNotesPopupWidget,
        OrderlineNoteButton: OrderlineNoteButton,
    }

});
