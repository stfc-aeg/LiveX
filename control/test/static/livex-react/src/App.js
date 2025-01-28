import './App.css';

import 'odin-react/dist/index.css'
import 'bootstrap/dist/css/bootstrap.min.css';

import Container from 'react-bootstrap/Container';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';
import Button from 'react-bootstrap/Button';

import PidControl from './components/furnace/PidControl';
import ThermalGradient from './components/furnace/ThermalGradient';
import AutoSetPointControl from './components/furnace/AutoSetPointControl';
import FurnaceRecording from './components/furnace/FurnaceRecording';
import Motor from './components/furnace/Motor';
import React from "react";
import { OdinApp } from 'odin-react';
import { WithEndpoint, useAdapterEndpoint } from 'odin-react';
import Metadata from './components/setup/Metadata';
import Cameras from './components/cameras/Cameras';
import Trigger from './components/setup/Trigger';
import MonitorGraph from './components/furnace/MonitorGraph';
import InfoPanel from './components/furnace/InfoPanel';

const EndPointButton = WithEndpoint(Button);

function App(props) {

  // axios.defaults.baseURL = process.env.REACT_APP_ENDPOINT_URL;

  const endpoint_url = process.env.REACT_APP_ENDPOINT_URL;

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
        <Container>
          <Row className="d-flex justify-content-between">
            <Col xs="auto">
              <EndPointButton
                endpoint={furnaceEndPoint}
                value={true}
                fullpath="status/reconnect"
                event_type="click"
                disabled={!connectedPuttingDisable}
                variant={furnaceEndPoint.data.status?.connected ? "primary" : "danger"}>
                {furnaceEndPoint.data.status?.connected ? 'Connected' : 'Reconnect'}
              </EndPointButton>
            </Col>
            <Col xs="auto">
              <EndPointButton
                endpoint={furnaceEndPoint}
                value={true}
                fullpath="status/full_stop"
                event_type="click"
                disabled={connectedPuttingDisable}
                variant='danger'>Disable all outputs
              </EndPointButton>
            </Col>
          </Row>
        </Container>
        <Col xs={12} lg={6} xl={6} xxl={6}>
          <PidControl
            furnaceEndPoint={furnaceEndPoint}
            connectedPuttingDisable={connectedPuttingDisable}
            title="Upper Heater (A) Controls"
            pid="pid_a">
          </PidControl>

          <PidControl
            furnaceEndPoint={furnaceEndPoint}
            connectedPuttingDisable={connectedPuttingDisable}
            title="Lower Heater (B) Controls"
            pid="pid_b">
          </PidControl>

          <FurnaceRecording
            furnaceEndPoint={furnaceEndPoint}>
          </FurnaceRecording>

        </Col>
        <Col lg={6} xl={6} xxl={6}>
          <ThermalGradient
            furnaceEndPoint={furnaceEndPoint}
            connectedPuttingDisable={connectedPuttingDisable}>
          </ThermalGradient>

          <AutoSetPointControl
            furnaceEndPoint={furnaceEndPoint}
            connectedPuttingDisable={connectedPuttingDisable}>
          </AutoSetPointControl>

          <Motor
            furnaceEndPoint={furnaceEndPoint}
            connectedPuttingDisable={connectedPuttingDisable}>
          </Motor>

          <InfoPanel
            furnaceEndPoint={furnaceEndPoint}
            connectedPuttingDisable={connectedPuttingDisable}>
          </InfoPanel>
        </Col>
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
              {dataPath: 'temperature_c', param: 'data', seriesName: "TC3"},
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