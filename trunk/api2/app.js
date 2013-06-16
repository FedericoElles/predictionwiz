// ----------- //
// APPLICATION //
// ----------- //

var app = angular.module('app',['ui.directives','ui.bootstrap']).
  config(function($routeProvider) {
    $routeProvider.
      when('/', {controller:MainCtrl, templateUrl:'main.html'}).
      when('/dict', {controller:DictCtrl, templateUrl:'dict.html'}).

      otherwise({redirectTo:'/'});
  });
  
  
app.filter('urlencode', function () {
        return function (text) {
            if (typeof text != "undefined"){
				return encodeURIComponent(text)
            } else {return ""}
        };
    });

app.filter('nonewline', function () {
        return function (text) {
            if (typeof text != "undefined"){
				return text.replace(/\n/g,'')
            } else {return ""}
        };
    });
	
function DictCtrl($scope, $location, $http, $timeout) {
	$scope.ctrl={}
	$scope.params = {} 
	$scope.params.appName = ''
	$scope.params.dictName= ''
	$scope.params.setKey= ''
	$scope.params.getKey= ''
	$scope.params.value= ''
	$scope.params.massValue= ''
	
	$scope.set = {"available":false}
	$scope.get = {"available":false}
	$scope.massSet = {"available":false,"queue":[],"success":0}

	
	var LSKEY =  "predictionwizv2api-"

	if (localStorage.getItem(LSKEY+'params')){
		$scope.params = JSON.parse(localStorage.getItem(LSKEY+'dictparams'))
	}
	$scope.$watch('params',function(newval,oldval){
		localStorage.setItem(LSKEY+'dictparams',JSON.stringify(newval))
	},true)

	$scope.ctrl.emptyParamsSet = function(){
		var r = false
		if ($scope.params.appName == '') r = true
		if ($scope.params.dictName == '') r = true
		if ($scope.params.setKey == '') r = true
		if ($scope.params.value == '') r = true
		return r
	}
	
	$scope.ctrl.emptyParamsGet = function(){
		var r = false
		if ($scope.params.appName == '') r = true
		if ($scope.params.dictName == '') r = true
		if ($scope.params.getKey == '') r = true
		return r
	}	
	
	$scope.ctrl.emptyParamsMassSet = function(){
		var r = false
		if ($scope.params.appName == '') r = true
		if ($scope.params.dictName == '') r = true
		if ($scope.params.massValue == '') r = true

		return r
	}		

	$scope.apiSet = function(){
		var url = fixURL($('#urlSet').html(),$scope.params.appName)
		$scope.set.available=false
		$scope.set.loading=true
		//console.log('apiCreate.url',url)
		$http.get(url).then(
			function(response) {
				console.log('apiSet',response)
				$scope.set.available=true
				$scope.set.loading=false
				$scope.set.result = response.data
			},
			function(response){
				console.log('apiSet.failed',response)
				$scope.set.available=true
				$scope.set.loading=false
				$scope.set.result = response.data
			}
			
		)
	 
	 }
	
	$scope.apiGet = function(){
		var url = fixURL($('#urlGet').html(),$scope.params.appName)
		$scope.get.available=false
		$scope.get.loading=true
		//console.log('apiCreate.url',url)
		$http.get(url).then(
			function(response) {
				console.log('apiGet',response)
				$scope.get.available=true
				$scope.get.loading=false
				$scope.get.result = response.data
			},
			function(response){
				console.log('apiGet.failed',response)
				$scope.get.available=true
				$scope.get.loading=false
				$scope.get.result = response.data
			}
			
		)
	 
	 }	


	//mass set
	
	$scope.getLines=function(txt){
        if (typeof txt != "undefined"){
			return txt.split('\n').length
		} else {
			return 0
		}
	}
	
	$scope.apiMassSet=function(){
		//reset variables
		$scope.massSet.success=0
		$scope.massSet.queue=[]
		//load records to queue
		var txt = $scope.params.massValue
		if (txt !== ""){
			var a = txt.split('\n')
			for (var i=0,ii=a.length;i<ii;i+=1){
				var rec = a[i]
				var aRec = rec.split(',') //TODO this will not work for "a,a","result"
				if (aRec.length>1){
					var key = aRec.shift()
					var value = aRec.join(',')
				}
				console.log('apiMassSet.record',key,value)
				$scope.massSet.queue.push({"key":key,"value":value})
			}
			startQueue()
		}
	}


	var startQueue = function(){
		if ($scope.massSet.queue.length>0){
			$timeout(processQueue,500) 
		}
	}
	
	var processQueue = function(){
		if ($scope.massSet.queue.length>0){
			var rec = $scope.massSet.queue.shift()
			console.log('processQueue.record',rec.key,rec.value)
			var url = fixURL('https://'+$scope.params.appName+'.appspot.com/'+
			  'dict/'+encodeURIComponent($scope.params.dictName)+
			  '/set?key='+encodeURIComponent(rec.key)+
			  '&value='+encodeURIComponent(rec.value),$scope.params.appName)
			
			$http.get(url).then(
				function(response) {
					console.log('processQueue.success',response)
					$scope.massSet.success += 1
				},
				function(response){
					console.log('processQueue.failed',response)
				}
			)
			startQueue()
		}
	}
	 

	 
}	
  
function MainCtrl($scope, $location, $http) {
	$scope.ctrl={}
	$scope.create = {"available":false}
	$scope.status = {"available":false}
	$scope.update = {"available":false}
	$scope.predict = {"available":false}
	
	var LSKEY =  "predictionwizv2api-"
	
	//PARAMETERS
	$scope.params = {} 
	$scope.params.appName = ''
	$scope.params.hashKey = ''
	$scope.params.bucketName = ''
	$scope.params.fileName = ''
	$scope.params.fileContent = ''
	if (localStorage.getItem(LSKEY+'params')){
		$scope.params = JSON.parse(localStorage.getItem(LSKEY+'params'))
	}
	$scope.$watch('params',function(newval,oldval){
		localStorage.setItem(LSKEY+'params',JSON.stringify(newval))
	},true)
	
	$scope.ctrl.emptyParams = function(){
		var r = false
		if ($scope.params.appName == '') r = true
		if ($scope.params.hashKey == '') r = true
		if ($scope.params.bucketName == '') r = true
		if ($scope.params.fileName == '') r = true
		if ($scope.params.fileContent == '') r = true
		return r
	}
	
	$scope.apiCreate = function(){
		var url = fixURL($('#urlCreate').html(),$scope.params.appName)
		$scope.create.available=false
		$scope.create.loading=true
		//console.log('apiCreate.url',url)
		$http.get(url).then(
			function(response) {
				console.log('apiCreate',response)
				$scope.create.available=true
				$scope.create.loading=false
				var data = response.data
				$scope.create.result = data
				$scope.create.result.json = JSON.stringify(data)
			},
			function(response){
				console.log('apiCreate.failed',response)
				$scope.create.available=true
				$scope.create.loading=false
				$scope.create.result = {"response":JSON.stringify(response)}
			}
			
		)
		
		/*$http.get('foo.json').success(function(data) {
			console.log('apiCreate',data)
			$scope.create.available=true
			$scope.create.loading=false
			var data = data
			$scope.create.result = data
		}).error(function(){
			$scope.create.available=true
			$scope.create.loading=false
			$scope.create.result
			
		});*/

	 
	 }
} 

	//detect if running on dev environment	 
	var fixURL=function(url,appname){
		if (location.href.indexOf("localhost")>-1){
			url = url.replace("https://"+appname+".appspot.com","http://"+location.host)
		}
		return url
	 }