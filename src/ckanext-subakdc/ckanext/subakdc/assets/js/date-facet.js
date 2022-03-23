"use strict";

this.ckan.module('date_facet', function ($) {
    return {
        initialize: function () {

        var facet = this.el;

        // Params from current URL query string
        var params = new URLSearchParams(location.search);

        // Date input fields
        var startDateInput = facet.find("input[name='subak_temporal_start']");
        var endDateInput = facet.find("input[name='subak_temporal_end']");
        
        // Set the date inputs based on params in query string, or set to default values
        startDateInput.val(params.get('subak_temporal_start') || 1900);
        endDateInput.val(params.get('subak_temporal_end') || new Date().getUTCFullYear());
        
        // Update query string when clicking the update button
        facet.find('button#date-facet-update').on("click", function() {    
            params.set('subak_temporal_start', startDateInput.val());
            params.set('subak_temporal_end', endDateInput.val());
            location.href = location.pathname + '?' + params.toString();
        });

        // Update query string when clicking the reset button
        facet.find('button#date-facet-reset').on("click", function() {
            params.delete('subak_temporal_start');
            params.delete('subak_temporal_end');
            location.href = location.pathname + '?' + params.toString();
        });
    }
  };
})