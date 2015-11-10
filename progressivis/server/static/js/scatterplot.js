var margin = {top: 20, right: 20, bottom: 30, left: 40},
    width = 960 - margin.left - margin.right,
    height = 500 - margin.top - margin.bottom,
    svg, firstTime = true;

var x = d3.scale.linear()
    .range([0, width]);

var y = d3.scale.linear()
    .range([height, 0]);

var color = d3.scale.category10();

var xAxis = d3.svg.axis()
    .scale(x)
    .orient("bottom");

var yAxis = d3.svg.axis()
    .scale(y)
    .orient("left");

const DEFAULT_SIGMA = 2;
const DEFAULT_FILTER = "default";

const MAX_PREV_IMAGES = 4;
var prevImages = []; //keeps references to previous images for comparison

/**
 * Enqueues an image in the prevImages array.
 * Invariant: prevImages contains at most MAX_PREV_IMAGES + 1 elements
 * (we store the current image as well as the previous ones)
 */
function enqueue(elem){
  if(prevImages.length === MAX_PREV_IMAGES + 1){
    prevImages = prevImages.slice(1);
  }
  prevImages.push(elem);
}


function scatterplot_update(data) {
    module_update(data);
    scatterplot_update_vis(data);
}

function scatterplot_update_vis(rawdata) {
    var data = rawdata['scatterplot'],
        bounds = rawdata['bounds'];

    if (!data || !bounds) return;
    var index = data['index'];
    x.domain([bounds['xmin'], bounds['xmax']]).nice();
    y.domain([bounds['ymin'], bounds['ymax']]).nice();

    if (firstTime) {
        svg.append("rect")
            .attr("x", 0)
            .attr("y", 0)
            .attr("width", width)
            .attr("height", height)
            .attr("fill", "black");

        svg.append("image")
            .attr("class", "heatmap")
            .attr("xlink:href", rawdata['image'])
            .attr("preserveAspectRatio", "none")
            .attr("x", 0)
            .attr("y", 0)
            .attr("width", width)
            .attr("height", height)
            .attr("filter", "url(#gaussianBlur)");

        svg.append("image")
           .attr("class", "heatmapCompare")
           .attr("preserveAspectRatio", "none")
           .attr("opacity", 0.5)
           .attr("x", 0)
           .attr("y", 0)
           .attr("width", width)
           .attr("height", height);

        svg.append("g")
            .attr("class", "x axis")
            .attr("transform", "translate(0," + height + ")")
            .call(xAxis)
            .append("text")
            .attr("class", "label")
            .attr("x", width)
            .attr("y", -6)
            .style("text-anchor", "end")
            .text([0]);

        svg.append("g")
            .attr("class", "y axis")
            .call(yAxis)
            .append("text")
            .attr("class", "label")
            .attr("transform", "rotate(-90)")
            .attr("y", 6)
            .attr("dy", ".71em")
            .style("text-anchor", "end")
            .text(data['columns'][1]);
        firstTime = false;
    }
    else { // not firstTime
        svg.select(".heatmap")
            .attr("xlink:href", rawdata['image']);

        svg.select(".x.axis")
            //.transition()
            //.duration(1000)
            .call(xAxis);

        svg.select(".y.axis")
            //.transition()
            //.duration(100)
            .call(yAxis);
    }
    var imgSrc = rawdata['image'];
    if(prevImages.indexOf(imgSrc) === -1){
      enqueue(imgSrc);
    }

    var prevImgElements = d3.select("#prevImages").selectAll("img")
      .data(prevImages.slice(0,-1)); //we omit the last element (current image)

      prevImgElements.enter()
      .append("img")
      .attr("width", 100)
      .attr("height", 100)
      .on("mouseover", function(d){
        d3.select(".heatmapCompare")
          .attr("xlink:href", d)
          .attr("visibility", "inherit");
      })
      .on("mouseout", function(d){
        d3.select(".heatmapCompare")
          .attr("visibility", "hidden");
      });

      prevImgElements.attr("src", function(d){ return d; });

    var dots = svg.selectAll(".dot")
            .data(data['data'], function(d, i) { return index[i]; });
    
    dots.enter().append("circle")
         .attr("class", "dot")
         .attr("r", 3.5)
         .attr("cx", function(d) { return x(d[0]); })
         .attr("cy", function(d) { return y(d[1]); })
         .style("fill", "blue") //function(d) { return color(d.species); });
        .append("title")
        .text(function(d, i) { return index[i]; });
    dots//.transition()  // Transition from old to new
        //.duration(500)  // Length of animation
         .attr("cx", function(d) { return x(d[0]); })
         .attr("cy", function(d) { return y(d[1]); });    
    dots.exit().remove();
}

function scatterplot_refresh() {
  module_get(scatterplot_update, error);
}


/**
 * @param select - a select element that will be mutated 
 * @param names - list of option names (the value of an option is set to its name)
 */
function makeOptions(select, names){
  if(!select){
    console.warn("makeOptions requires an existing select element");
    return;
  }
  names.forEach(function(name){
    var option = document.createElement("option");
    option.setAttribute("value", name);
    option.innerHTML = name;
    select.appendChild(option);
  });
}

function scatterplot_ready() {
    svg = d3.select("#scatterplot svg")
         .attr("width", width + margin.left + margin.right)
         .attr("height", height + margin.top + margin.bottom)
        .append("g")
         .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    $('#nav-tabs a').click(function (e) {
        e.preventDefault();
        $(this).tab('show');
    });

    const gaussianBlur = document.getElementById("gaussianBlurElement");
    const filterSlider = $("#filterSlider");
    filterSlider.change(function(){
      gaussianBlur.setStdDeviation(this.value, this.value);
    });
    filterSlider.get(0).value = DEFAULT_SIGMA;
    gaussianBlur.setStdDeviation(DEFAULT_SIGMA, DEFAULT_SIGMA);

    const colorMap = document.getElementById("colorMap");
    const colorMapSelect = $("#colorMapSelect");
    colorMapSelect.change(function(){
      colormaps.makeTableFilter(colorMap, this.value);
    });
    colorMapSelect.get(0).value = DEFAULT_FILTER;
    makeOptions(colorMapSelect.get(0), colormaps.getTableNames());
    
    refresh = scatterplot_refresh; // function to call to refresh
    module_ready();
}
