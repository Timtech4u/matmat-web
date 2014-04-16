var QUESTIONS_IN_SET = 10;
var INITIAL_WAIT_TIME_BEFORE_Q_FINISH = 1000;
var FADEOUT_DURATION = 500;
var QUESTIONS_IN_QUEUE = 1; // 0 - for load Q when needed. 1 - for 1 waiting Q, QUESTIONS_IN_SET - for load all Q on start

app.config(function($locationProvider) {
        $locationProvider.html5Mode(true);
});

app.controller("Loader", function($scope, $cookies, CommonData, $http, $compile, $location){
    $scope.common = CommonData;
    $scope.skill_id = $location.search().skill;
    $scope.question = null;
    $scope.counter = {
        total: QUESTIONS_IN_SET,
        current: 0
    };

    $scope.questions_queue = [];

    $scope.get_questions_from_server = function(){
        var count = Math.min(QUESTIONS_IN_QUEUE - $scope.questions_queue.length,
            QUESTIONS_IN_SET - $scope.counter.current - $scope.questions_queue.length);
        count += $scope.question == null ? 1 : 0;

        if (count > 0){
            $http.get("/q/get_question/", {params: {count:count, skill:$scope.skill_id} })
                .success(function(data){
                    $scope.questions_queue = $scope.questions_queue.concat(data);
                    $scope.get_question();
            });
        }
    };

    $scope.get_question = function(){
        if ($scope.question == null && $scope.questions_queue.length > 0){
            $scope.question = $scope.questions_queue.shift();
            $scope.question.log = [];
            var questionDirective = angular.element(
                '<{0} interface=\'interface\' data=\'{1}\' />'
                    .format($scope.question.simulator.replace("_",""), $scope.question.data));
            $("#playground").append(questionDirective);
            $compile(questionDirective)($scope);
            $scope.question.start_time = new Date().getTime();
            $scope.loading = false;
        }
        $scope.get_questions_from_server();
    };

    $scope.save_answer = function(){
        $http.post("/q/save_answer/", $scope.question)
            .success(function(data){
                $scope.chat = data;
            });
    };


    $scope.next_question = function(){
        $scope.loading = true;
        $scope.counter.current++;
        $scope.get_question()
    };


    $scope.finish_question = function(correctly_solved, wait_time){
        wait_time = typeof wait_time !== 'undefined' ? wait_time : INITIAL_WAIT_TIME_BEFORE_Q_FINISH;

        $scope.log_something("finished");
        setTimeout(function() {
            $scope.question.time =  Math.round((new Date().getTime() - $scope.question.start_time) / 1000);
            $scope.question.correctly_solved =  correctly_solved;
            $scope.save_answer();


            $scope.question.hide = true;
            setTimeout(function() {
                $("#playground").empty();
                $scope.question = null;
                if ($scope.counter.current == $scope.counter.total){
                    window.location.replace("/");
                }else{
                    $scope.next_question();
                }
            }, FADEOUT_DURATION);
        }, wait_time);
    };

    $scope.skip = function(){
        $scope.log_something("skipped");
        $scope.finish_question(false, 0);
    };

    $scope.log_something = function(data){
        $scope.question.log.push([(new Date().getTime() - $scope.question.start_time), data]);
//        console.log($scope.question.log);
    };


    $scope.interface = {};
    $scope.interface.finish = $scope.finish_question;
    $scope.interface.log = $scope.log_something;

    $scope.next_question();


});
