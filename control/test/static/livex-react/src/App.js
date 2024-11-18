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

const EndPointButton = WithEndpoint(Button);

function App(props) {

  const endpoint_url = process.env.REACT_APP_ENDPOINT_URL

  const furnaceEndPoint = useAdapterEndpoint('furnace', endpoint_url, 1000);
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
            endpoint={furnaceEndPoint}
            seriesData={[
              {dataPath: 'temperature', param: 'temperature_a', seriesName: "TCA"},
              {dataPath: 'temperature', param: 'temperature_b', seriesName: "TCB"},
              {dataPath: 'temperature', param: 'temperature_c', seriesName: "TC3"},
              {dataPath: 'setpoint', param: 'setpoint_a', seriesName: "SPA"},
              {dataPath: 'setpoint', param: 'setpoint_b', seriesName: "SPB"}
            ]}
            title={"Temperature and Setpoint Graph"}
          ></MonitorGraph>
        </Col>
        <Col xs={12} sm={12} xl={6} xxl={6}>
          <MonitorGraph
            endpoint={furnaceEndPoint}
            seriesData={[
              {dataPath: 'output', param: 'output_a', seriesName: 'POA'},
              {dataPath: 'output', param: 'output_b', seriesName: 'POB'}
            ]}
            title={"PID Output Graph"}
          ></MonitorGraph>
        </Col>
      </Row>
    </OdinApp>
  );
}

export default App;