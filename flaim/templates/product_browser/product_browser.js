axios.get("/api/products")
    .then(function (response) {
        console.log(response)
    })
    .catch(function (error) {
        console.log(error)
    })
    .finally(function () {
        console.log("finally")
    });
