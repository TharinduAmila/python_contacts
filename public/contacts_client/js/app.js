var app = angular.module('app', ['ngRoute', 'toastr', 'ngCookies']);

app.service('server', ["$cookies", "$http", "$rootScope", "$location", "toastr", function ($cookies, $http, $rootScope, $location, toastr) {
    let host = "http://localhost:5000/";

    function setTokenDetails(data) {
        $rootScope.accessToken = data.accessToken;
        $rootScope.refreshToken = data.refreshToken;
        $rootScope.user = data.user.fname;
        $cookies.put("accessToken", $rootScope.accessToken);
        $cookies.put("refreshToken", $rootScope.refreshToken);
        $cookies.put("user", $rootScope.user);
    }

    function refreshToken(callback) {
        $http({
            method: 'PUT',
            url: host + 'user/login',
            headers: {
                'Authorization': "Bearer " + $rootScope.refreshToken
            },
        }).then(function successCallback(response) {
            response.data['user'] = {'fname': $rootScope.user}
            setTokenDetails(response.data);
            callback();
        }, function errorCallback(response) {
            console.log("err", response);
            postLogOffCleanUp();
        });
    }

    function postLogOffCleanUp() {
        $rootScope.$broadcast("loggedOff");
        toastr.info("You have been logged off");
        $rootScope.accessToken = undefined;
        $rootScope.refreshToken = undefined;
        $rootScope.user = undefined;
        $cookies.remove("accessToken");
        $cookies.remove("refreshToken");
        $cookies.remove("user");
        $location.url("login");
    }

    this.login = function (email, password, callback) {
        $http({
            method: 'POST',
            url: host + 'user/login',
            data: {
                "email": email,
                "password": password
            }
        }).then(function successCallback(response) {
            setTokenDetails(response.data);
            $rootScope.$broadcast('isLoggedIn');
            $location.url('');
        }, function errorCallback(response) {
            if (response.data && response.data.message) {
                toastr.error(response.data.message, 'Failed to Login');
            } else {
                toastr.error("Please contact admin", 'Failed to Login');
            }
            callback();
        });
    };
    this.logout = function () {
        if (this.isLoggedIn()) {
            $http({
                method: 'DELETE',
                url: host + 'user/login',
                headers: {
                    'Authorization': "Bearer " + $rootScope.accessToken
                },
            }).then(function successCallback() {
                postLogOffCleanUp();
            }, function errorCallback(response) {
                console.log("err", response);
                postLogOffCleanUp();
            });
        } else {
            $location.url("login");
        }
    };
    this.signup = function (email, password, fname, mname, lname, telephone, callback) {
        let userDetails = {
            "email": email,
            "fname": fname,
            "password": password,
            "telephone": telephone
        };
        if (mname) {
            userDetails["mname"] = mname;
        }
        if (lname) {
            userDetails["lname"] = lname;
        }
        $http({
            method: 'POST',
            url: host + 'user',
            data: userDetails
        }).then(function successCallback(response) {
            setTokenDetails(response.data);
            $rootScope.$broadcast('isLoggedIn');
            $location.url('');
        }, function errorCallback(response) {
            if (response.data && response.data.message) {
                var info = response.data.data || {};
                if (info.telephone) {
                    toastr.error("Telephone number is " + response.data.data.telephone, 'Failed to Signup');
                } else if (info.email) {
                    toastr.error("Email is " + response.data.data.email, 'Failed to Signup');
                } else {
                    toastr.error(response.data.message, 'Failed to Signup');
                }
            } else {
                toastr.error("Please contact admin", 'Failed to Signup');
            }
            callback(info);
        });
    };
    this.isLoggedIn = function () {
        if ($rootScope.accessToken && $rootScope.refreshToken) {
            return true;
        } else if ($cookies.get("accessToken") && $cookies.get("refreshToken")) {
            setTokenDetails({
                accessToken: $cookies.get("accessToken"),
                refreshToken: $cookies.get("refreshToken"),
                user: {fname: $cookies.get("user")}
            });
            $rootScope.$broadcast('isLoggedIn');
            return true;
        } else {
            return false;
        }
    };

    this.addContact = function addContact(contactEmail, callback, retry = false) {
        $http({
            method: 'POST',
            url: host + 'contacts/' + encodeURIComponent(contactEmail),
            headers: {
                'Authorization': "Bearer " + $rootScope.accessToken
            }
        }).then(function successCallback(response) {
            toastr.success("Contact added");
            callback();
        }, function errorCallback(response) {
            console.log("err", response);
            if (response.status == 401) {
                if (!retry) {
                    refreshToken(() => {
                        addContact(contactEmail, callback, true);
                    });
                } else {
                    toastr.error("Please login and try again");
                    postLogOffCleanUp();
                }
            } else {
                toastr.error("Bad request.");
                callback();
            }
        });
    };
    this.removeContact = function removeContact(contactEmail, callback, retry = false) {
        $http({
            method: 'DELETE',
            url: host + 'contacts/' + encodeURIComponent(contactEmail),
            headers: {
                'Authorization': "Bearer " + $rootScope.accessToken
            }
        }).then(function successCallback(response) {
            toastr.success("Contact removed");
            callback();
        }, function errorCallback(response) {
            console.log("err", response);
            if (response.status == 401) {
                if (!retry) {
                    refreshToken(() => {
                        removeContact(contactEmail, callback, true);
                    });
                } else {
                    toastr.error("Please login and try again");
                    postLogOffCleanUp();
                }
            } else {
                toastr.error("Bad request.");
                callback();
            }
        });
    };
    this.getContacts = function getContacts(callback, retry = false) {
        $http({
            method: 'GET',
            url: host + 'contacts',
            headers: {
                'Authorization': "Bearer " + $rootScope.accessToken
            },
        }).then(function successCallback(response) {
            callback(null, response.data)
        }, function errorCallback(response) {
            console.log("err", response);
            if (response.status == 401) {
                if (!retry) {
                    refreshToken(() => {
                        getContacts(callback, true);
                    });
                } else {
                    toastr.error("Please login and try again");
                    postLogOffCleanUp();
                }
            } else {
                toastr.error("Bad request.");
                callback();
            }
        });
    };
    this.getRecommendedContacts = function getRecommendedContacts(callback, retry) {
        $http({
            method: 'GET',
            url: host + 'contacts/recommendations',
            headers: {
                'Authorization': "Bearer " + $rootScope.accessToken
            },
        }).then(function successCallback(response) {
            callback(null, response.data)
        }, function errorCallback(response) {
            console.log("err", response);
            if (response.status == 401) {
                if (!retry) {
                    refreshToken(() => {
                        getRecommendedContacts(callback, true);
                    });
                } else {
                    toastr.error("Please login and try again");
                    postLogOffCleanUp();
                }
            } else {
                toastr.error("Bad request.");
                callback();
            }
        });
    };
    this.findUsers = function findUsers(searchString, callback, retry = false) {
        $http({
            method: 'GET',
            url: host + 'user?search=' + searchString,
            headers: {
                'Authorization': "Bearer " + $rootScope.accessToken
            },
        }).then(function successCallback(response) {
            callback(null, response.data)
        }, function errorCallback(response) {
            console.log("err", response);
            if (response.status == 401) {
                if (!retry) {
                    refreshToken(() => {
                        findUsers(searchString, callback, true);
                    });
                } else {
                    toastr.error("Please login and try again");
                    postLogOffCleanUp();
                }
            } else {
                toastr.error("Bad request.");
                callback();
            }
        });
    };

}]);


app.config(['$routeProvider', function ($routeProvider) {
    $routeProvider
        .when('/login', {
            templateUrl: "templates/login.htm", controller: 'login', resolve: {
                isLoggedIn: (server, $location) => {
                    if (server.isLoggedIn()) {
                        $location.url("");
                    }
                }
            }
        })
        .when('/signup', {
            templateUrl: 'templates/signup.htm', controller: 'signup', resolve: {
                isLoggedIn: (server, $location) => {
                    if (server.isLoggedIn()) {
                        $location.url("");
                    }
                }
            }
        })
        .when('/', {
            templateUrl: 'templates/mainView.htm', controller: 'mainView', resolve: {
                isLoggedIn: (server, $location) => {
                    if (!server.isLoggedIn()) {
                        $location.url("login");
                    }
                }
            }
        })
        .otherwise({
            redirectTo: '/login'
        });
}]);

app.config(function (toastrConfig) {
    angular.extend(toastrConfig, {
        autoDismiss: true,
        containerId: 'toast-container',
        maxOpened: 1,
        newestOnTop: true,
        positionClass: 'toast-top-right',
        preventDuplicates: false,
        preventOpenDuplicates: false,
        target: 'body',
        timeOut: 2000
    });
});

app.controller('login', ["$scope", "$http", "server",
    function ($scope, $http, server) {
        $scope.login = function () {
            if ($scope.email && $scope.password) {
                server.login($scope.email, $scope.password, () => {
                    $scope.email = '';
                    $scope.password = '';
                });
            }
        }
    }]);
app.controller('signup', ["$scope", "server", function ($scope, server) {
    $scope.busy = false;
    $scope.signup = function () {
        if ($scope.busy) {
            return false;
        }
        $scope.busy = true;
        if ($scope.email && $scope.password) {
            $scope.telInvalid = false;
            $scope.emailInvalid = false;
            server.signup($scope.email, $scope.password, $scope.fname, $scope.mname, $scope.lname, $scope.telephone,
                (data) => {
                    $scope.busy = false;
                    if (data.email) {
                        $scope.email = "";
                        $scope.emailInvalid = true;
                    }
                    if (data.telephone) {
                        $scope.telephone = "";
                        $scope.telInvalid = true;
                    }
                });
        }
    }
}]);

app.controller('mainView', ["$scope", "$route", "server", "toastr", function ($scope, $route, server, toastr) {
    $scope.$on("$viewContentLoaded", () => {
        $scope.users = null;
        $scope.recommendations = [];
        $scope.contacts = [];
        $scope.busy = false;

        server.getContacts((err, response) => {
            if (response && response.data) {
                $scope.contacts = response.data;
            }
        });
        server.getRecommendedContacts((err, response) => {
            if (response && response.data) {
                $scope.recommendations = response.data;
            } else {
                $scope.recommendations = [];
            }
        });
    });
    $scope.searchAll = ($event) => {
        $event.preventDefault();
        $scope.busy = true;
        if (!$scope.searchString) {
            toastr.info("Please enter a search string");
            $scope.busy = false;
        } else {
            server.findUsers($scope.searchString, function (err, response) {
                if (response && response.data) {
                    $scope.users = response.data;
                } else {
                    $scope.users = null;
                }
                $scope.busy = false;
            });
        }
    };
    $scope.clearSearchResult = ($event) => {
        $event.preventDefault();
        if ($scope.busy) {
            toastr.info("Please wait until your previous action is completed");
            return false;
        }
        $scope.users = null;
        $scope.searchString = "";
    };
    $scope.addContact = ($event, email) => {
        $event.preventDefault();
        if ($scope.busy) {
            toastr.info("Please wait until your previous action is completed");
            return false;
        }
        $scope.busy = true;
        server.addContact(email, () => {
            $route.reload();
        });
    };
    $scope.removeContact = ($event, email) => {
        $event.preventDefault();
        if ($scope.busy) {
            toastr.info("Please wait until your previous action is completed");
            return false;
        }
        $scope.busy = true;
        server.removeContact(email, () => {
            $route.reload();
        });
    };
}]);

app.controller('nav', ["$scope", "$location", "server", function ($scope, $location, server) {
    $scope.logout = function ($event) {
        $event.preventDefault();
        server.logout();
    };
    $scope.inSignUp = function () {
        return $location.path() == '/signup'
    };
    $scope.loggedIn = false;
    $scope.$on('isLoggedIn', function () {
        $scope.loggedIn = true;
    });
    $scope.$on('loggedOff', function () {
        $scope.loggedIn = false;
    });
}]);