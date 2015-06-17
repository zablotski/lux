
    angular.module('lux.grid', ['lux.message', 'templates-grid', 'ngTouch', 'ui.grid', 'ui.grid.pagination', 'ui.grid.selection', 'angularMoment'])
        //
        .constant('gridDefaults', {
            showMenu: true,
            gridMenu: {
                'create': {
                    title: 'Add',
                    icon: 'fa fa-plus'
                },
                'delete': {
                    title: 'Delete',
                    icon: 'fa fa-trash'
                }
            }
        })
        //
        // Directive to build Angular-UI grid options using Lux REST API
        .directive('restGrid', ['$lux', '$window', '$modal', '$state', '$q', '$message', 'uiGridConstants', 'gridDefaults',
            function ($lux, $window, $modal, $state, $q, $message, uiGridConstants, gridDefaults) {

            var paginationOptions = {
                    sizes: [25, 50, 100]
                },
                gridState = {
                    page: 1,
                    limit: 25,
                    offset: 0,
                };

            function parseColumns(columns) {
                var columnDefs = [],
                    column;

                angular.forEach(columns, function(col) {
                    column = {
                        field: col.field,
                        displayName: col.displayName,
                        type: getColumnType(col.type),
                    };

                    if (!col.hasOwnProperty('sortable'))
                        column.enableSorting = false;

                    if (!col.hasOwnProperty('filter'))
                        column.enableFiltering = false;

                    if (column.field === 'id')
                        column.cellTemplate = '<div class="ui-grid-cell-contents"><a ng-href="{{grid.appScope.objectUrl(COL_FIELD)}}">{{COL_FIELD}}</a></div>';

                    if (column.type === 'date') {
                        column.cellTemplate = '<div style="color:red;">{{COL_FIELD | amDateFormat:"YYYY-MM-DD HH:mm:ss"}}</div>';
                        column.sortingAlgorithm = function(a, b) {
                            var dt1 = new Date(a).getTime(),
                                dt2 = new Date(b).getTime();
                            return dt1 === dt2 ? 0 : (dt1 < dt2 ? -1 : 1);
                        };
                    } else if (column.type === 'boolean') {
                        column.cellTemplate = '<div class="ui-grid-cell-contents"><i ng-class="{{COL_FIELD == true}} ? \'fa fa-check-circle text-success\' : \'fa fa-times-circle text-danger\'"></i></div>';

                        if (col.hasOwnProperty('filter')) {
                            column.filter = {
                                type: uiGridConstants.filter.SELECT,
                                selectOptions: [{ value: 'true', label: 'True' }, { value: 'false', label: 'False'}],
                            };
                        }
                    }
                    columnDefs.push(column);
                });

                return columnDefs;
            }

            // Get initial data
            function getInitialData (scope) {
                var api = $lux.api(scope.options.target),
                    sub_path = scope.options.target.path || '';

                api.get({path: sub_path + '/metadata'}).success(function(resp) {
                    gridState.limit = resp['default-limit'];

                    scope.gridOptions.columnDefs = parseColumns(resp.columns);

                    api.get({path: sub_path}, {limit: gridState.limit}).success(function(resp) {
                        scope.gridOptions.totalItems = resp.total;
                        scope.gridOptions.data = resp.result;
                    });
                });
            }

            // Get specified page using params
            function getPage(scope, api, params) {
                api.get({}, params).success(function(resp) {
                    scope.gridOptions.totalItems = resp.total;
                    scope.gridOptions.data = resp.result;
                });
            }

            // Return column type accirding to type
            function getColumnType(type) {
                switch (type) {
                    case 'integer':     return 'number';
                    case 'datetime':    return 'date';
                    default:            return type;
                }
            }

            function addGridMenu(scope, api, gridOptions) {
                var menu = [],
                    stateName = $state.current.url.split('/').pop(-1),
                    model = stateName.slice(0, -1),
                    modalScope = scope.$new(true),
                    modal,
                    title;

                scope.create = function($event) {
                    $state.go($state.current.name + '_add');
                };

                scope.delete = function($event) {
                    var modalTitle, modalContent,
                        pk = gridOptions.columnDefs[0].field,
                        icon = '<i class="fa fa-trash"></i>',
                        modalTemplate = 'grid/modal.tpl.html',
                        results = [],
                        success = false;

                    scope.selected = scope.gridApi.selection.getSelectedRows();

                    if (!scope.selected.length) {
                        modalTitle = icon + ' Lack of ' + stateName + ' to delete';
                        modalContent = 'Please, select some ' + stateName + '.';
                        modalTemplate = 'grid/modal.empty.tpl.html';
                    } else {
                        modalTitle = icon + ' Delete ' + stateName;
                        modalContent = 'Are you sure you want to delete ' + stateName;

                        forEach(scope.selected, function(item) {
                            results.push(item[pk]);
                        });

                        results = results.join(',');
                        modalContent += ' ' + results + '? This cannot be undone!';
                    }

                    modal = $modal({scope: modalScope, title: modalTitle, content: modalContent, template: modalTemplate, show: true});

                    modalScope.ok = function() {
                        var defer = $q.defer();
                        forEach(scope.selected, function(item, _) {
                            api.delete({path: '/' + item[pk]})
                                .success(function(resp) {
                                    success = true;
                                    defer.resolve(success);
                                });
                        });

                        defer.promise.then(function() {
                            if (success) {
                                getPage(scope, api, gridState);
                                $message.success('Successfully deleted ' + stateName + ' ' + results);
                            } else
                                $message.error('Error while deleting ' + stateName + ' ' + results);

                            modal.hide();
                        });
                    };
                };

                forEach(gridDefaults.gridMenu, function(item, key) {
                    title = item.title;

                    if (key === 'create')
                        title += ' ' + model;

                    menu.push({
                        title: title,
                        icon: item.icon,
                        action: scope[key]
                    });
                });

                extend(gridOptions, {
                    enableGridMenu: true,
                    gridMenuShowHideColumns: false,
                    gridMenuCustomItems: menu
                });
            }

            // Pre-process grid options
            function buildOptions (scope, options) {
                scope.options = options;

                scope.objectUrl = function(objectId) {
                    return $window.location + '/' + objectId;
                };

                var api = $lux.api(options.target),
                    gridOptions = {
                        paginationPageSizes: paginationOptions.sizes,
                        paginationPageSize: gridState.limit,
                        enableFiltering: true,
                        enableRowHeaderSelection: false,
                        useExternalPagination: true,
                        useExternalSorting: true,
                        rowHeight: 30,
                        onRegisterApi: function(gridApi) {
                            scope.gridApi = gridApi;
                            scope.gridApi.pagination.on.paginationChanged(scope, function(pageNumber, pageSize) {
                                gridState.page = pageNumber;
                                gridState.limit = pageSize;
                                gridState.offset = pageSize*(pageNumber - 1);

                                getPage(scope, api, gridState);
                            });

                            scope.gridApi.core.on.sortChanged(scope, function(grid, sortColumns) {
                                if( sortColumns.length === 0) {
                                    delete gridState.sortby;
                                    getPage(scope, api, gridState);
                                } else {
                                    // Build query string for sorting
                                    angular.forEach(sortColumns, function(column) {
                                        gridState.sortby = column.name + ':' + column.sort.direction;
                                    });

                                    switch( sortColumns[0].sort.direction ) {
                                        case uiGridConstants.ASC:
                                            getPage(scope, api, gridState);
                                            break;
                                        case uiGridConstants.DESC:
                                            getPage(scope, api, gridState);
                                            break;
                                        case undefined:
                                            getPage(scope, api, gridState);
                                            break;
                                    }
                                }
                            });
                        }
                    };

                if (gridDefaults.showMenu)
                    addGridMenu(scope, api, gridOptions);

                return gridOptions;
            }

            return {
                restrict: 'A',
                link: {
                    pre: function (scope, element, attrs) {
                        var scripts= element[0].getElementsByTagName('script');

                        forEach(scripts, function (js) {
                            globalEval(js.innerHTML);
                        });

                        var opts = attrs;
                        if (attrs.restGrid) opts = {options: attrs.restGrid};

                        opts = getOptions(opts);

                        if (opts) {
                            scope.gridOptions = buildOptions(scope, opts);
                            getInitialData(scope);
                        }
                    },
                },
            };

        }]);
