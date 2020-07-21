import React from 'react';
import {Input} from 'antd';
import {SearchOutlined} from '@ant-design/icons';

const SearchBar = () => {
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
            onSearch={value => console.log(value)}
        />

    )
}

export default SearchBar
