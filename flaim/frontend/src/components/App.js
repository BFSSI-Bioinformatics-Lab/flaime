import React from "react";
import {BrowserRouter, Route} from "react-router-dom";
import {Layout} from 'antd';

import 'antd/dist/antd.css'
import './App.css'

import Reports from "./Reports";
import Tools from "./Tools";
import Navbar from "./Navbar"
import Home from "./Home";
import Data from "./Data";
import About from "./About";


const {Header, Footer, Content} = Layout;

const App = () => {
    return (
        <BrowserRouter>
            <Layout className="layout">

                <Header>
                    <Navbar/>
                </Header>

                <Content style={{padding: '0 50px'}}>
                    <div className="site-layout-content">
                        <Route path="/v2" exact component={Home}/>
                        <Route path="/v2/reports" exact component={Reports}/>
                        <Route path="/v2/tools" exact component={Tools}/>
                        <Route path="/v2/data" exact component={Data}/>
                        <Route path="/v2/about" exact component={About}/>
                    </div>
                </Content>

                <Footer>
                    Footer
                </Footer>

            </Layout>
        </BrowserRouter>

    )
}

export default App

