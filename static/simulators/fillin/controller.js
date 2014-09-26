app.directive("fillin", function(){
    return {
        restrict: "E",
        scope: {
            data: "=data",
            interface: "=interface"
        },
        templateUrl: static_url + "simulators/fillin/simulator.html",
        controller: function($scope, CommonData){
            $scope.fill = '_';
            $scope.answer = CommonData.input;
            $scope.answer.value = '';
            $("#simulator-input").focus();

            if ($scope.data.answer <= 10){
                CommonData.keyboard = "choices";
                CommonData.choices = _.range(1, 11);
            }else{
                CommonData.keyboard = "full";
            }

            $scope.check_answer = function(){
                $scope.answer.value = $scope.answer.value.replace(/\s*-\s*/g,'-').trim();
                var correct = $scope.answer.value == $scope.data.answer;
                var wait = correct ? 1000 : 3000;
                $scope.solved = true;
                $("#playground").find("input").prop('disabled', true);
                $scope.interface.finish(correct, wait);
            };
            CommonData.submit = $scope.check_answer;

            $scope.change = function(){
                $scope.interface.log($scope.answer.value);
                $scope.fill = ($scope.answer == '') ? '_' : $scope.answer;
            };
        }
    }
});
