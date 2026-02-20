function analyzeText() {
    const text = document.getElementById("textInput").value;

    fetch("/analyze", {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({text:text})
    })
    .then(res=>res.json())
    .then(data=>{
        document.getElementById("result").innerHTML =
        `<h3>Sentiment: ${data.sentiment}</h3>`;
        location.reload();
    });
}

// Pie Chart
new Chart(document.getElementById("pieChart"), {
    type:"pie",
    data:{
        labels:["Positive","Negative","Neutral"],
        datasets:[{
            data:[positive,negative,neutral],
            backgroundColor:["#00ff88","#ff4d4d","#f1c40f"]
        }]
    }
});

// Monthly Trend
new Chart(document.getElementById("barChart"), {
    type:"bar",
    data:{
        labels:Object.keys(monthlyData),
        datasets:[{
            label:"Monthly Feedback Count",
            data:Object.values(monthlyData),
            backgroundColor:"#3498db"
        }]
    }
});