// Create a scaling relations plot using Plotly
var linecolor = 'rgba(0, 0, 0, 0.2)';
var zerolinecolor = 'rgba(0, 0, 0, 0.4)';

var makeScalingPlot = function(plotID, plotLabel, xFit, yFit, xData, yData, xLabel, yLabel, outTypeX, outTypeY, annotations) {
    scalingPlot = document.getElementById(plotID);
    Plotly.plot(scalingPlot, [{
        x: xFit,
        y: yFit,
        // name: 'Linear Fit',
        name: plotLabel,
        mode: 'lines',
        // marker: {color:'grey'}
        marker: {
            color: 'rgba(0, 0, 0, 0.25)'
        }
    }, {
        x: xData,
        y: yData,
        showlegend: false,
        type: 'scatter',
        name: '',
        text: annotations,
        mode: 'markers',
        marker: {
            color: 'rgba(91, 191, 224, 1.0)'
        }
    }], {
        // title: '{{ fit_label }}',
        xaxis: {
            title: 'E'.italics() + outTypeX.sub() + xLabel,
            showline: true,
            zerolinecolor: zerolinecolor,
            linecolor: linecolor,
            tickcolor: linecolor,
            mirror: 'allticks',
            ticks: 'inside',
        },
        yaxis: {
            title: 'E'.italics() + outTypeY.sub() + yLabel,
            showline: true,
            zerolinecolor: zerolinecolor,
            linecolor: linecolor,
            tickcolor: linecolor,
            mirror: 'allticks',
            ticks: 'inside',
        },
        legend: {
            xanchor: "center",
            yanchor: "top",
            x: 0.5,
            y: 1.12
        },
        margin: {
            t: 10
        },
        hovermode: 'closest'
    });
}