App.View.Form = Backbone.View.extend({

    tagName: 'div',

    className: 'content',

    events: {
        'click button': 'submit',
    },

    initialize: function(options) {
        this.$el.hide();
        var template = App.renderTemplate('form', this.model.toJSON());
        options.parent.$el.find('#content').append(this.el);
        this.$el.append(template);
        this.model.on('change', this.render, this);
        App.EventAggregator.on('clear:form', this.clear, this);
    },

    submit: function() {
        var formData = new FormData($('form')[0]);
        $.ajax({
            url: App.SERVER + '/extract',
            type: 'PUT',
            data: formData,
            // Tell jQuery not to process data or worry about content-type.
            cache: false,
            contentType: false,
            processData: false,
            success: function(data) {
                App.router.navigate(
                    'results/' + data.extraction_id,
                    { trigger: true }
                );
            },
            error: function(data) {
                debugger;
            }
        });
    }
});
