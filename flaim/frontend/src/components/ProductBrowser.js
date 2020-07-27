import React from 'react';
import ProductTable from "./ProductTable";
import SearchBar from "./SearchBar";
import useProductSearch from "../hooks/useProductSearch";

const ProductBrowser = () => {
    const [products, search] = useProductSearch('')

    return (
        <div>
            <SearchBar onSearch={search}/>
            <ProductTable data={products.results}/>
        </div>
    )
}

export default ProductBrowser
