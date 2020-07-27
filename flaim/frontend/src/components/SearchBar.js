import React, {useState} from 'react';
import {Input} from 'antd';
import {SearchOutlined} from '@ant-design/icons';

// Takes a custom search hook and pipes the value from the search bar into it
const SearchBar = ({onSearch}) => {

    const suffix = (
        <SearchOutlined
            style={{
                fontSize: 20,
                color: '#1890ff',
            }}
        />
    );

    const {Search} = Input;

    return (
        <Search
            placeholder="input search text"
            enterButton="Search"
            size="large"
            suffix={suffix}
            onSearch={(value) => onSearch(value)}
        />

    )
}

export default SearchBar
