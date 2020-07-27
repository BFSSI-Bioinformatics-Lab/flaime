import React, {useState, useEffect} from 'react';
import axios from 'axios';
import api from "../apis/api";
import DataTable from 'react-data-table-component';


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

const ProductTablePaginated = () => {
    const [data, setData] = useState([])
    const [loading, setLoading] = useState(false)
    const [totalRows, setTotalRows] = useState(0)
    const [perPage, setPerPage] = useState(10)


    const fetchProducts = async page => {
        const response = await api.get(`/recent_products/?page=${page}`, {
                params: {
                    query: term,
                }
            }
        )
        setProducts(response.data)
    }


    const fetchUsers = async page => {
        setLoading(true)

        const response = await axios.get(
            `https://reqres.in/api/users?page=${page}&per_page=${perPage}&delay=1`,
        )

        setData(response.data.data)
        setTotalRows(response.data.total)
        setLoading(false)
    }

    const handlePageChange = page => {
        fetchUsers(page)
    }

    const handlePerRowsChange = async (newPerPage, page) => {
        setLoading(true)

        const response = await axios.get(
            `https://reqres.in/api/users?page=${page}&per_page=${newPerPage}&delay=1`,
        )

        setData(response.data.data);
        setPerPage(newPerPage)
        setLoading(false)
    };

    useEffect(() => {
        fetchUsers(1)

    }, [])

    return (
        <DataTable
            title="Users"
            columns={columns}
            data={data}
            progressPending={loading}
            pagination
            paginationServer
            paginationTotalRows={totalRows}
            selectableRows
            onChangeRowsPerPage={handlePerRowsChange}
            onChangePage={handlePageChange}
        />
    )
}

export default ProductTablePaginated
