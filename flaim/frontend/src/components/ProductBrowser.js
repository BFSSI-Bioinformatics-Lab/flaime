import React, {useState} from 'react';
import api from "../apis/api";

const ProductBrowser = () => {
    const [products, setProducts] = useState([])

    const search = async term => {
        const response = await api.get('/recent_products', {
                params: {
                    query: term,
                }
            }
        )

        console.log(response)
    }

    search('beef')

    return (
        <div>
            <h1>product browser</h1>
        </div>
    )
}

export default ProductBrowser
