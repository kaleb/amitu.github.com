---
layout: page
title: "angularjs"
description: ""
---
{% include JB/setup %}

#### Background And Personal Biases

* This is a [spark style](/) post \[In which I write a bunch of bullets about
  everything I know/think about a given topic\]. This is also my first post of
  this style so lets see how it goes.

* One of the first things I noticed about angularjs was that it was advertised
  to be by google. It may mean nothing or it may mean that it is something
  good, it piqued my interest, and when I saw half a dozen backbone and other
  "modern" javascript libraries, this was the first I gave my real attention
  to. And I feel it totally paid off.

* There is a trend of "modern" javascript libraries. This trend is mostly
  towards frontend, yet it is kind of triggered by nodejs, a server side
  framework. I guess it is because a lot of "serious" develpers looked in
  javascript after nodejs proved that not only javascript can be used in server
  side programming, it may be beat quite a few existing way of doing web from
  performance point of view. Well, be what may, lots of new developers picked
  javascript essentials book, and realized javascript sucks and modern
  javascript libraries were born.

* My personal bias: I learnt about "modern" javascript libraries thru backbone.
  For my hammerd project, Harsh suggested I should release as backbone backend
  for hammerd. I did not like backbone at all.

* My personal bial: I started learning dojo, in fact I started writing a book
  to teach myself dojo, I am two chapter into it. I think dojo is one of the
  best libraries for javascript. It gives class. It allows modular programming
  in javascript. It gives a rather rich set of widgets. It gives a lot of other
  utilities javascript developers need. Dojo according to me a full stack
  library, it does nearly everything, and does it well, consistently, and is
  very very modern.

* JQuery is the most used javascript library. But it is just a few DOM
  utilities, some bare minimal AJAX wrapper and few other nicities. Without
  jquery javascript programming is torturous. And it is damn easy to learn.
  Dojo is better, it does more, your dojo programms are going to be an order of
  magnitude better compared to your jquery programs. But dojo has a learning
  curve. So jquery wins. And it has massive collection of user contributed
  plugins. Tho many, external plugin, jquery-s strength, they are are
  inconsistent, take me or leave me kind of affair. jquery ecosystem is like
  PHP ecosystem, a lot of "functions", with no underlying structure. If jquery
  is php, dojo is django.

#### Understanding angularjs

* Best way to understand angularjs is to see angular not so much as a
  javascript library but as enhanced HTML.

* HTML is declarative. If you want something bold, you surround it with STRONG
  tag. If you want an input to be readonly, you add a readonly attribute to
  INPUT tag. These tags or attributes are called directives in angular
  terminology.

* Angular lets you create new directives(html tags or html attributes). Using
  javascript. You can create new tags and attributes, and give it special
  meaning using angularjs, and the designers can then use those tags.

* Unlike other template based javascript frameworks, like mustache, angular
  does not deal with string templates. The DOM tree constructed by browser is
  the "template" for angular. Which makes it important that the "template" be
  valid HTML, and for old browsers that do not allow creation of new tags
  special strategies have to be used, called "shimming".

* Angular has a "compile" phase, in which it goes through the DOM looking for
  special directives angular or we defined. Angular starts from "angular root"
  node, which typically is HTML node, but it can be any node. Angular finds
  this node and inspects closely all children DOM nodes, their tag names, their
  attributes and their TEXT nodes.

* ng-app is the only required directive. This is used as an attribute, on any
  DOM node, add ng-app attribute to mark it as "angular root" for the page.
  There can only be one "angular root" in a page, so usually it is a good idea
  to make HTML the root node: &lt;html ng-app&gt;. Since agnular "compiler"
  does extensive analysis of every child of root node, it may be desirable in
  some cases to make some other DIV etc the root node to reduce the amount of
  processing angular has to do: &lt;div ng-app&gt;.

* Before the "compile" phase begins, angular loads main "modules". If no
  "module" is specified as main module, "angular" is considered the main
  module. To specify the name of the module pass it as the value of ng-app
  attribute: &lt;html ng-app="myapp"&gt;

* Angular is "modular", but modules in angular should not be confused with
  modules in AMD. It is a good idea to still use AMD with angular, and the name
  module might be confusing.

* "module" in angular is a internal namespace. What happens is this: any module
  can define some directives, for example lets say in my defines a module
  called amitu-app, and in this app I defined a directive named amitu-widget.
  Now my application can do &lt;html ng-app="amitu-app"&gt; that tells angular
  to use all directives defined in amitu-app, eg amitu-widget, and make it
  available to for this application.

* An example directive. Here we are creating a directive called "clicker". Once
  the directive is created it can be used anywhere in HTML (within angular
  root). [demo](/angularjs/clicker.html).

{% highlight html %}
<!doctype html>
<html ng-app="amitu-clicker">
  <head>
    <script src="/angularjs/angular.min.js"></script>
    <script>
        angular.module("amitu-clicker", []).
            directive("clicker", function() {
                return function(scope, element, attrs) {
                    element.bind("click", function(){
                        console.log("click");
                    });
                }
            });
    </script>
  </head>
  <body>
      <a href="#" clicker>clicker</a>
  </body>
</html>
{% endhighlight %}

* Things to note in this example:

  1. There is ng-app attribute set on &lt;HTML&gt; node telling angular that
  our root element is HTML node.

  1. The value of ng-app is set to "amitu-clicker", this is going to be our
  "main module".

  1. We have created a new module "amitu-clicker" by using the method
  "angular.module". This method takes the name of the module to be created as
  first parameter, and second parameter is a list of modules my module depends
  on. In this case we do not depend on anything yet.

  1. angular.module returns a "module object", on this object we have invoked
  the method named "directive". This is how new directives are defined.

  1. .directive() method takes name of the directive and either an object or a
  function as second parameter. In this case we have invoked it with a function
  as second parameter. A much richer api is vailable to us when we pass an
  object as second parameter, but in this case we want a simple directive, and
  we need not bother with other parameters, so we used the function instead.

  1. So directives go through two phases, one is called compile phase and other
  is called link phase. I have previously said the DOM is "template" from
  angular point of view. So a DOM node may represent either an actual node, or
  it may represent multiple nodes, for example in case of a repeater. So I can
  create a directive that takes the DOM in html and creates a lot of DOM nodes.
  That phase is called compile phase. Most of the times I do not want to do
  that, and instead I want to leave the DOM as it is, and just add some
  behaviours to it, this is called link phase.

  1. When we called .directive with function as second argument, angular
  assumed we do not want to do any compile time magic, and just want to add
  some behaviour, and it considered our function the link function. If we do
  want to alter the DOM, I would have passed a configuration object as second
  parameter, this object will have a compile function, a link function, and a
  set of other attributes to assist angular.

  1. So we have passed a name of the directive to be created and the link
  function to angular. Angular then goes on and compiles the DOM, checks if
  "clicker" attribute is present on any DOM element, and if it is present calls
  our link function for each element found.

  1. Our link function gets three arguments, scope, we will discuss this a bit
  later, the DOM node that the directive is on, and normalized attributes.

  1. Why do we have to normalize attribute? Angularjs allows a variety of
  naming convention, data-clicker is also allowed, and directives can be
  mentioned in class list of element or even in comments. Since attribute can
  be anywhere, attrs provides a convenient normalized way to access them.

  1. In this example if tried to put our directive as tag
  name(&lt;clicker&gt;&lt;/clicker&gt;) or in class name(&lt;a href="#"
  class="clicker:;"&gt;) or in comment(&lt;!-- directive: clicker --&gt;), it
  will fail, as we have defined the directive with link function only, and by
  default angular only checks for attribute. If we want these forms we can
  invoke directive with an object, as we will see later.

  1. The element that is passed to our callback is a referance to DOM node, but
  it is wrapped by $() if jquery is included in the page, else it is wrapped in
  mini jquery like emulation layer included in angular. Angular detects
  presence of jquery in the page on page load time.

  1. In our example we have used element.bind api, to handle a click handler.

  1. Please also note that ng-app attribute on HTML matches with the name of
  the module we defined. If we use a module that doesn-t exist, as we did not
  create angular.module(module_name, []) for it, we will get an error.

  1. The real value of angular is that once an attribute is implemented and
  debugged, designers can use it like any other html attribute they use.

* modules can depend on each other, so amitu-app can depend on amitu-ui,
  amitu-grid etc, and directives defined in each of those modules will then
  become available to me.

* It is still my responsibility to make sure my page includes the javascript
  file that defines my module and the directive. And all the other modules that
  my module depends on. It would be a good idea to use requirejs or dojo-s AMD
  facility to manage the modules. The dependencies would have to duplicated, as
  AMD dependency is specified differently compared to angular module
  dependency. There is nothing stopping me from writing all my angular modules
  in a single javascript file, but it is not a good practice for large complex
  applications.

* So far I have only talked about directives, but there are other concepts in
  angular that are defined on module level, for example filters, and
  "services". We will come to them later.

* Angular also has a concept of expressions. The point of dynamic html with
  javascript is to show some data in javascript, and we usually us $.text()
  function in jquery to do that. This is cumbersome, we have to decide what DOM
  elements the data will go to when writing javascript. So we use \{\{ somedata
  \}\} like expressions in angular.
