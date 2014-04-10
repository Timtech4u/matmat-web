app.directive("example", function(){
    /* name of directive have to be its name without _  (replaced by "") */
    return {
        restrict: "E",
        scope: {
            data: "=data",              // json data from database
            interface: "=interface"     // interface of loader
        },
        templateUrl: static_url + "simulators/example/simulator.html",  // html
        controller: function($scope){
                /*
                    During solving log interesting actions
                 */
                $scope.interface.log("log something this way");

            $scope.answer = function(answer){
                $scope.interface.log("answer was " + answer);

                /* at the end call finish with
                    - true or false depending of correctness of answer
                    - optional time of waiting before loading next question. Initial 1000ms
                 */
                $scope.interface.finish(answer, 1234);
            }

        }
    }
});
