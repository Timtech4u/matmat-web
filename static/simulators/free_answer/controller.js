app.directive("freeanswer", function(){
    return {
        restrict: "E",
        scope: {
            data: "=data",
            next: "=next"
        },
        templateUrl: static_url + "simulators/free_answer/simulator.html",
        controller: function($scope){
            $scope.okHidden = true;
            $scope.nokHidden = true;

            $scope.check_answer = function(){
                $scope.okHidden = !($scope.answer == $scope.data.answer);
                $scope.nokHidden = ($scope.answer == $scope.data.answer);

                setTimeout(function() {
                    $scope.next();
                }, 700);

            };
//          TODO - logging
        }
    }
});
