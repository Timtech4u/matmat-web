var app = angular.module('matmat', ["ngCookies", "ngAnimate"]);

app.factory("CommonData", function(){
        return {
            test: "hello world",

//            for simulators
            submit: null,                   // function which ends question in simulator
            skip: null,                     // function which skip question in simulator
            simulator_active: false,        // indicate if simulator is active
            input: {"value": ""},           // current input
            keyboard: 'gone',               // keyboard mode
            log_something: null,            // simulator logger
            get_simulator_list: null,       // list of selected simulator pk
            clear_queue: null                // clear questions from queue
        }
    }
);

app.config(function($httpProvider){
        $httpProvider.defaults.xsrfCookieName = 'csrftoken';
        $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    }
);