import './App.css';

// import 'odin-react/dist/index.css'
import 'bootstrap/dist/css/bootstrap.min.css';

import Container from 'react-bootstrap/Container';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';
import Button from 'react-bootstrap/Button';

import FurnacePage from './components/furnace/FurnacePage';
import { OdinApp } from 'odin-react';
import { WithEndpoint, useAdapterEndpoint } from 'odin-react';
import Metadata from './components/setup/Metadata';
import Cameras from './components/cameras/Cameras';
import Trigger from './components/setup/Trigger';
import MonitorGraph from './components/furnace/MonitorGraph';

// import plotly from 'plotly.js-dist-min';


function App(props) {

  // axios.defaults.baseURL = process.env.REACT_APP_ENDPOINT_URL;

  const endpoint_url = import.meta.env.VITE_ENDPOINT_URL;

  const furnaceEndPoint = useAdapterEndpoint('furnace', endpoint_url, 1000);
  const graphEndPoint = useAdapterEndpoint('graph', endpoint_url, 1000);
  const connectedPuttingDisable = (!(furnaceEndPoint.data.status?.connected || false)) || (furnaceEndPoint.loading === "putting")

  const sequencer_url = endpoint_url + "/sequencer.html";

  return (
    <OdinApp title="LiveX Controls" navLinks={["Metadata and Setup", "Sequencer", "Furnace Control", "Camera Control", "Monitoring"]}>
      <Row>
        <Col xs={12}>
          <Metadata
            endpoint_url={endpoint_url}
            connectedPuttingDisable={connectedPuttingDisable}>
          </Metadata>
        </Col>
        <Col xs={12}>
          <Trigger
            endpoint_url={endpoint_url}>
          </Trigger>
        </Col>
      </Row>
      <Row>
        <h4><a href={sequencer_url} target="_blank">Click here</a> to open sequencer (in new tab)</h4>
      </Row>
      <Row>
        <FurnacePage
          furnaceEndPoint={furnaceEndPoint}
          connectedPuttingDisable={connectedPuttingDisable}
        />
      </Row>
      <Row>
        <Cameras
          endpoint_url={endpoint_url}
          connectedPuttingDisable={connectedPuttingDisable}>
        </Cameras>
      </Row>
      <Row>
        <Col xs={12} sm={12} lg={12} xl={6} xxl={6}>
          <MonitorGraph
            endpoint={graphEndPoint}
            seriesData={[
              {dataPath: 'temperature_a', param: 'data', seriesName: "TCA"},
              {dataPath: 'temperature_b', param: 'data', seriesName: "TCB"},
              {dataPath: 'setpoint_a', param: 'data', seriesName: "SPA"},
              {dataPath: 'setpoint_b', param: 'data', seriesName: "SPB"}
            ]}
            title={"Temperature and Setpoint Graph"}
          ></MonitorGraph>
        </Col>
        <Col xs={12} sm={12} xl={6} xxl={6}>
          <MonitorGraph
            endpoint={graphEndPoint}
            seriesData={[
              {dataPath: 'output_a', param: 'data', seriesName: 'POA'},
              {dataPath: 'output_b', param: 'data', seriesName: 'POB'}
            ]}
            title={"PID Output Graph"}
          ></MonitorGraph>
        </Col>
      </Row>
    </OdinApp>
  );
}

export default App;