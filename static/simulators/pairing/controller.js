app.directive("pairing", function(){
    return {
        restrict: "E",
        scope: {
            data: "=data",
            interface: "=interface"
        },
        templateUrl: template_urls["pairing"],
        controller: function($scope, SimulatorGlobal){
            $scope.gameover = false;
            SimulatorGlobal.keyboard = "empty";


            var q = $scope.data.question;
            $scope.todo = q.length;
            var cells = [];
            for (var i=0; i < q.length; i++) {
                var pair = q[i];
                for (var j=0; j < pair.length; j++) 
                    cells.push({'text': pair[j], 'pair': i,
                                'disabled': false, 'state': 'active'});
            }
            cells = _.shuffle(cells);
            $scope.rows = [];
            for (var i=0; i <= 2; i++) {
                var row = [];
                for (var j=0; j < q.length; j++) {
                   row.push(cells.pop());
                }
               $scope.rows.push(row);
            } 

            $scope.selected = undefined;
            $scope.click = function(cell) {
                if ($scope.selected == undefined) {
                    // select
                    $scope.interface.log("SELECT: " + cell.text);
                    $scope.selected = cell;
                    $scope.selected.state = 'selected';
                } else if ($scope.selected == cell) {
                    // unselect
                    $scope.interface.log("UNSELECT: " + cell.text);
                    $scope.selected.state = 'active';
                    $scope.selected = undefined;
                } else if ($scope.selected.pair == cell.pair) {
                    // correct
                    $scope.interface.log("CORRECT: " + cell.text);
                    $scope.selected.disabled = true;
                    cell.disabled = true;
                    $scope.selected.state = 'off';
                    cell.state = 'off';
                    $scope.selected = undefined;
                    $scope.todo--;
                    if ($scope.todo == 1) {
                        $scope.submit(true);
                    }
                } else {
                    // wrong
                    $scope.interface.log("WRONG: " + cell.text);
                    $scope.selected.state = 'wrong';
                    cell.state = 'wrong';
                    $scope.selected = undefined;
                    $scope.submit(false);
                }
                console.log($scope);
            }

            $scope.submit = function(correct) {
                $scope.gameover = true;
                var wait = correct ? 1000 : 3000;
                $scope.solved = correct;
                $scope.interface.finish(correct, wait);
            };
            SimulatorGlobal.submit = $scope.submit;

            $scope.change = function(){
                $scope.interface.log("lala");
            };

            SimulatorGlobal.description.top = "Vyznač kartičky se stejnou hodnotou."
        }
    }
});
