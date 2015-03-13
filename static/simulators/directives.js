app.directive('focus', function(){
    return function(scope, element){
        if (device == "desktop"){
            element[0].focus();
        }else{
            element[0].blur();
        }
    };
});

app.directive("keyboard", function($timeout){
    return {
        restrict: "E",
        scope: {
        },
        templateUrl: template_urls["keyboard"],
        controller: function($scope, $cookieStore, SimulatorGlobal){
            //  $scope.hidden = !$cookieStore.get("keyboard");
            $scope.hidden = false;
            $scope.global = SimulatorGlobal;

            $scope.submit = function(){
                SimulatorGlobal.submit();
            };

            $scope.submit_answer = function(answer){
                if (!$scope.global.simulator_active)
                    return;
                $scope.add_text(answer);
                $scope.submit();
            };

            // change response after click to keyboard
            $scope.add_text = function(s){
                if (!$scope.global.simulator_active)
                    return;
                var value = $scope.global.input.value;
                if (s == 'larr'){
                    $scope.global.input.value = value.substring(0, $scope.global.input.value.length - 1);
                }else{
                    $scope.global.input.value = value + s;
                }
                $scope.global.log_something("soft-kyeborad:"+s);
                $scope.global.log_something($scope.global.input.value)
            };

            $scope.skip = function(){
                SimulatorGlobal.skip();
            };

            $scope.switch_visibility = function(){
                $("#keyboard-buttons").addClass("animate-show-drop");
                if ($scope.hidden) {
                    $scope.hidden = false;
                    $cookieStore.put("keyboard", true);
                }else{
                    $scope.hidden = true;
                    $cookieStore.put("keyboard", false);
                }
            };
        }
    }
});

// input field with submit button
app.directive("responseinput", function($timeout){
    return {
        restrict: "E",
        scope: {
            ngModel: "=",       // model for input
            submit: "&",        // submit function
            ngChange: "&"       // function to call after input change
        },
        templateUrl: template_urls["response-input"],

        controller: function($scope, SimulatorGlobal){
            $scope.global = SimulatorGlobal;
            $scope.change = function(){
                $timeout($scope.ngChange, 0);
            }
        }
    }
});

// show current response, after finish question show correct solution
app.directive("responsespan", function(){
    return {
        restrict: "E",
        scope: {
            answer: "=",        // right answer
            response: "=",      // current response
            solved: "=",        // indicator of question finish
            default: "@"        // default string to show if answer is empty
        },
        templateUrl: template_urls["response-span"],
        controller: function($scope){
        }
    }
});


app.directive("simulatorselector", function(){
    return {
        restrict: "E",
        scope: {
        },
        templateUrl: template_urls["simulator-selector"],
        controller: function($scope, $cookieStore, SimulatorGlobal){
            $scope.simulators = simulators;

            for (var i=0; i<$scope.simulators.length; i++){
                var simulator = $scope.simulators[i];
                var state = $cookieStore.get("simulator" + simulator.pk);
                if (state == null)
                    state = true;
                simulator.selected = state;
            }

            $scope.change = function(simulator){
                $cookieStore.put("simulator" + simulator.pk, simulator.selected);
                SimulatorGlobal.clear_queue();
            };
        }
    }
});

app.directive("cubes", function(){
    return {
        restrict: "E",
        scope: {
            count: "=",        // right answer
            height: "=",        // right answer
            width: "="        // right answer
        },
        templateUrl: template_urls["cubes"],
        controller: function($scope){
            $scope.repeater = function(n) {
                return new Array(n);
            };
        }
    }
});