/**
 * Default Inyoka JavaScript Driver File
 * ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 *
 * Part of the Inyoka core framework. Provides default script
 * functions for the base templates.
 *
 * :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
 * :license: GNU GPL, see LICENSE for more details.
 */

var Inyoka = {

  getJSONServiceURL : function(identifier) {
    return this.SERVICE_ROOT + identifier + '/?format=json';
  },

  callJSONService : function(identifier, values, callback) {
    $.getJSON(this.getJSONServiceURL(identifier), values, callback);
  },

};
