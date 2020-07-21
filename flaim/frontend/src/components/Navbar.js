import React from 'react';
import {Link} from "react-router-dom";
import {Menu} from 'antd';
import {BarChartOutlined, ToolOutlined, DatabaseOutlined, QuestionCircleOutlined} from '@ant-design/icons';

import './Navbar.css'

const Navbar = () => {
    return (
        <div>
            <div className="logo"/>
            <Menu theme="dark" mode="horizontal" style={{textAlign: 'center'}}>
                <Menu.Item key="1" icon={<ToolOutlined/>}>
                    <Link to="/v2/tools">
                        Tools
                    </Link>
                </Menu.Item>
                <Menu.Item key="2" icon={<BarChartOutlined/>}>
                    <Link to="/v2/reports">
                        Reports
                    </Link>
                </Menu.Item>
                <Menu.Item key="3" icon={<DatabaseOutlined/>}>
                    <Link to="/v2/data">
                        Data
                    </Link>
                </Menu.Item>
                <Menu.Item key="4" icon={<QuestionCircleOutlined/>}>
                    <Link to="/v2/about">
                        About
                    </Link>
                </Menu.Item>
            </Menu>
        </div>
    )
}

export default Navbar
