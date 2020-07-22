import React from 'react'
import DataTable from 'react-data-table-component';


const ProductTable = ({data}) => {

    const columns = [
        {
            name: 'Name',
            selector: 'name',
            sortable: true,
        },
        {
            name: 'Brand',
            selector: 'brand',
            sortable: true,
        },
        {
            name: 'Store',
            selector: 'store',
            sortable: true,
        },
        {
            name: 'UPC',
            selector: 'upc_code',
            sortable: true,
        },
        {
            name: 'Scrape Date',
            selector: 'scrape_date',
            sortable: true,
        },
        {
            name: 'Price',
            selector: 'price',
            sortable: true,
        },
        {
            name: 'URL',
            selector: 'url',
            sortable: false,
        }
    ];

    return (
        <DataTable
            title="Products"
            columns={columns}
            data={data}
        />
    )
}

export default ProductTable
