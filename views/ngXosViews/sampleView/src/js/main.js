'use strict';

angular.module('xos.sampleView', [
  'ngResource',
  'ngCookies',
  'ui.router',
  'xos.helpers'
])
.config(($stateProvider) => {
  $stateProvider
  .state('user-list', {
    url: '/',
    template: '<users-list></users-list>'
  });
})
.config(function($httpProvider){
  $httpProvider.interceptors.push('NoHyperlinks');
})
.directive('usersList', function(){
  return {
    restrict: 'E',
    scope: {},
    bindToController: true,
    controllerAs: 'vm',
    templateUrl: 'templates/users-list.tpl.html',
    controller: function(Users){

      this.tableConfig = {
        resource: 'Users'
      };
      
    }
  };
});