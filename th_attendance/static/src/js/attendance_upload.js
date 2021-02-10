odoo.define('th_attendance.upload_attendance', function (require) {
"use strict";

    var AbstractAction = require('web.AbstractAction');
    var ControlPanelMixin = require('web.ControlPanelMixin');
    var base_import = require('base_import.import');
    var session = require('web.session');
    var time = require('web.time');
    var core = require('web.core');

    var QWeb = core.qweb;
    var _t = core._t;

    var SaveTemplateImport = base_import.DataImport.extend({
        init: function (parent, action) {
            this._super.apply(this, arguments);
            if (!this.res_model) {
                this.res_model = action.res_model;
                this.parent_context = action.context || {};
            }
        },
        onSaveTemplate: function () {
            var fields = this.$('.oe_import_fields input.oe_import_match_field').map(function (index, el) {
                return $(el).select2('val') || false;
            }).get();
            var columns = this.$('.oe_import_grid-header .oe_import_grid-cell .o_import_header_name').map(function () {
                return $(this).text().trim().toLowerCase() || false;
            }).get();
            let kwargs = {context: this.parent_context};
            return this._rpc({
                    model: 'base_import.import',
                    method: 'save_mapping',
                    args: [this.id, fields, columns],
                    kwargs : kwargs,
                }).then(function (data) {
                    alert("Save Template Successfully!!!")
                });
        },
        renderButtons: function() {
            var self = this;
            this.$buttons = $(QWeb.render("ImportSaveTemplate.buttons", this));
            this.$buttons.filter('.o_import_save_template').on('click', this.onSaveTemplate.bind(this));
            this.$buttons.filter('.oe_import_file').on('click', function () {
                self.$('.oe_import_file').click();
            });
            this.$buttons.filter('.o_import_cancel').on('click', function(e) {
                e.preventDefault();
                self.exit();
            });
        },
        onfile_loaded: function () {
            this._super.apply(this, arguments);
            this.$buttons.filter('.o_import_save_template').addClass('d-none');
        },
        onpreviewing: function () {
            this._super.apply(this, arguments);
            this.$buttons.filter('.o_import_save_template').addClass('d-none');
        },
        onpreview_error: function (event, from, to, result) {
            this._super.apply(this, arguments);
            this.$buttons.filter('.o_import_save_template').removeClass('d-none');
        },
        onpreview_success: function (event, from, to, result) {
            this._super.apply(this, arguments);
            this.$buttons.filter('.o_import_save_template').removeClass('d-none');
        }
    })

    core.action_registry.add('import_save', SaveTemplateImport);
    return {
        SaveTemplateImport: SaveTemplateImport
    }
});
