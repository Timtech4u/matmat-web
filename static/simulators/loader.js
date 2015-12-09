var QUESTIONS_IN_SET = 10;
var INITIAL_WAIT_TIME_BEFORE_Q_FINISH = 1000;
var FADEOUT_DURATION = 500;         // animation time after finish question
var FADEIN_DURATION = 500;         // animation time of showing question
var QUESTIONS_IN_QUEUE = 1; // 0 - for load Q when needed. 1 - for 1 waiting Q, QUESTIONS_IN_SET - for load all Q on start
var AUTO_NEXT_QUESTION = false;

app.controller("Loader", ["$scope", "$cookieStore", "SimulatorGlobal", "$http", "$compile", "$timeout", function($scope, $cookieStore, SimulatorGlobal, $http, $compile, $timeout){
    if ($scope.test){
        QUESTIONS_IN_QUEUE = 0;
        QUESTIONS_IN_SET = 10;
    }else{
        ga("send", "event", "set", "started", skill_name);
    }
    if (!$scope.test) $scope.skill_id = skill;         // selected skill from global
    $scope.question = null;                             // 17 question
    $scope.counter = {
        total: QUESTIONS_IN_SET,
        current: 0,
        progress: Array.apply(null, new Array(QUESTIONS_IN_SET)).map(Number.prototype.valueOf,0)
    };

    $scope.questions_queue = [];

    // get question from server
    $scope.get_questions_from_server = function(){
        // find out required question count
        var count = Math.min(QUESTIONS_IN_QUEUE - $scope.questions_queue.length,
            QUESTIONS_IN_SET - $scope.counter.current - $scope.questions_queue.length);
        count += $scope.question == null ? 1 : 0;

        if (count > 0){
            // find out question's pk already loaded (in queue or showed)
            var in_queue = [];
            if ($scope.question)
                in_queue.push($scope.question.pk);
            for (var i in $scope.questions_queue){
                in_queue.push($scope.questions_queue[i].pk);
            }

            if (!$scope.test) {
                $http.get("/q/get_question/",
                    {params: {
                        count: count,
                        skill: $scope.skill_id,
                        in_queue: in_queue.join(),
                        simulators: $scope.get_simulator_list()
                    } })
                    .success(function (data) {
                        for (var i in data) {
                            if (data[i].recommendation_log)
                                console.log(data[i]);
                        }
                        $scope.questions_queue = $scope.questions_queue.concat(data);
                        // try to show next question of any
                        $scope.get_question();
                    });
            }else{
                // fo simulator tester
                if ($scope.own_question){
                    q = {};
                    q.data = $scope.own_question;
                    q.simulator = $scope.simulator;
                    $scope.questions_queue.push(q);
                    $scope.get_question();
                }else {
                    $http.get("/q/get_selected_question/" + $scope.question_pk)
                        .success(function (data) {
                            for (var i in data) {
                                if (data[i].recommendation_log)
                                    console.log(data[i]);
                            }
                            $scope.questions_queue = $scope.questions_queue.concat(data);
                            $scope.get_question();
                        });
                }
            }
        }
    };

    // prepare next question or get it from server
    $scope.get_question = function(){
        if ($scope.question == null && $scope.questions_queue.length > 0){
            $scope.question = $scope.questions_queue.shift();
            $scope.question.log = [];

            // load question to playground
            var questionDirective = angular.element(
                '<{0} interface=\'interface\' data=\'{1}\' />'
                    .format($scope.question.simulator.replace("_",""), $scope.question.data));
            $compile(questionDirective)($scope);
            var playground =  $("#playground");
            if (playground.length > 0){
                playground.append(questionDirective);
            }else{
                $timeout(function() {
                    playground =  $("#playground");
                    playground.append(questionDirective);
                },100);
            }
        }
        $scope.get_questions_from_server();
    };

    // show and start prepared question
    SimulatorGlobal.simulator_loaded_callback = function(){
        if (SimulatorGlobal.keyboard == "full")
            $("responseinput").addClass("phantom");
        $scope.loading = false;
        $timeout(function(){
            $scope.question_description = SimulatorGlobal.description;
            $scope.question.start_time = new Date().getTime();
            SimulatorGlobal.simulator_active = true;
        },FADEIN_DURATION);
    };

    // send answer and log to server
    $scope.save_answer = function(){
        $scope.question.log = JSON.stringify($scope.question.log);
        if ($scope.test){
            console.log($scope.question);
            return;
        }
        $http.post("/q/save_answer/", $scope.question)
            .success(function(data){
                // console.log(data);
            });
    };

    // go to next question
    $scope.next_question = function(){
        $scope.loading = true;
        $scope.counter.current++;
        $scope.get_question()
    };

    $scope.finish_question = function(correctly_solved, answer, wait_time){
        if (!SimulatorGlobal.simulator_active){
            return;
        }
        SimulatorGlobal.simulator_active = false;
        wait_time = typeof wait_time !== 'undefined' ? wait_time : INITIAL_WAIT_TIME_BEFORE_Q_FINISH;

        $scope.log_something("finished");
        $scope.question.time =  (new Date().getTime() - $scope.question.start_time) / 1000;

        $scope.solved = correctly_solved ? "solved_correctly" : "solved_incorrectly";
        $scope.fast_solution = $scope.question.time <= $scope.question.expected_time * 2;
        $scope.extra_fast_solution = $scope.question.time <= $scope.question.expected_time;
        $scope.question.correctly_solved =  correctly_solved;
        $scope.say = correctly_solved ? "Správně" : "Špatně";
        if ($scope.extra_fast_solution && correctly_solved) $scope.say += " a rychle";
        $scope.question.answer =  answer;
        SimulatorGlobal.description.top = "";
        $scope.counter.progress[$scope.counter.current-1] = correctly_solved ? $scope.fast_solution ? $scope.extra_fast_solution ? 3 : 2 : 1 : -1;
        $timeout($scope.roller.fit_height, 0);

        $scope.save_answer();

        if (AUTO_NEXT_QUESTION || correctly_solved || answer === null) {
            // give time to show correct answer
            $timeout($scope.hide_question, wait_time);
        }else{
            SimulatorGlobal.hide_question = $scope.hide_question
        }
    };

    $scope.hide_question = function () {
        SimulatorGlobal.hide_question = null;
        $scope.question.hide = true;
        $scope.say = "";
        // wait to finish fade-out animation
        $timeout(function() {
            $("#playground").empty();
            $scope.question = null;
            if ($scope.counter.current == $scope.counter.total) {
                // if last question: redirect to "my skills" page
                if ($scope.test) {
                    $scope.counter.current = 1;
                    $scope.next_question();
                    return;
                }
                $scope.loading = true;
                ga("send", "event", "set", "finished", skill_name);
                $timeout(function () {
                    window.location.replace("/m/moje_vedomosti/" + $scope.skill_id);
                }, 0);
            } else {
                // load next question
                $scope.next_question();
            }
            $scope.solved = "";
        }, FADEOUT_DURATION);
    };

    $scope.save_partial_answer = function (correctly_solved, answer) {
        $scope.question.time =  (new Date().getTime() - $scope.question.start_time) / 1000;
        $scope.question.correctly_solved =  correctly_solved;
        $scope.question.answer =  answer;
        $scope.log_something("partial_solution");
        $scope.save_answer();
    };

    // skip question
    SimulatorGlobal.skip = $scope.skip = function(){
        $scope.log_something("skipped");
        if ($cookieStore.get('asked_to_skip', 0) > 0 || window.confirm("Opravdu chcete přeskočit tuto otázku?")){
            $cookieStore.put('asked_to_skip', $cookieStore.get('asked_to_skip', 0) + 1);
            $scope.finish_question(false, null, 0);
        }
    };

    // log step while solving process
    $scope.log_something = function(data){
        var log = [(new Date().getTime() - $scope.question.start_time), data];
        $scope.question.log.push(log);
        if ($scope.test) {
            console.log(log);
        }
    };
    SimulatorGlobal.log_something = $scope.log_something;

    // return list of simulator's pk as a string
    $scope.get_simulator_list = function(){
        var pks = [];
        for (var i=0; i < simulators.length; i++){
            var simulator = simulators[i];
            var state = $cookieStore.get("simulator" + simulator.pk);
            if (state || state==null){
                pks.push(simulator.pk);
            }
        }
        return pks.join();
    };

    // remove all preloaded questions
    $scope.clear_queue = function(){
        $scope.questions_queue = [];
    };
    SimulatorGlobal.clear_queue = $scope.clear_queue;

    $scope.roller = {};

    // define interface
    $scope.interface = {};
    $scope.interface.finish = $scope.finish_question;
    $scope.interface.save_partial_answer = $scope.save_partial_answer;
    $scope.interface.log = $scope.log_something;

    // start loading questions
    $scope.next_question();
}]);