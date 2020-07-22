import {useState, useEffect} from 'react'
import api from "../apis/api";

const useProductSearch = (searchTerm) => {
    const [products, setProducts] = useState([])

    useEffect(() => {
        search(searchTerm)
    }, [searchTerm])

    const search = async term => {
        const response = await api.get('/recent_products/', {
                params: {
                    query: term,
                }
            }
        )
        setProducts(response.data)
    }

    return [products, search]
}

export default useProductSearch
