import './App.css';

// import 'odin-react/dist/index.css'
import 'bootstrap/dist/css/bootstrap.min.css';

import Container from 'react-bootstrap/Container';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';
import Button from 'react-bootstrap/Button';

import FurnacePage from './components/furnace/FurnacePage';
import { OdinApp } from 'odin-react';
import { useAdapterEndpoint } from 'odin-react';
import Metadata from './components/setup/Metadata';
import Cameras from './components/cameras/Cameras';
import Trigger from './components/setup/Trigger';
import InferencePage from './components/InferencePage.jsx';
import GraphPage from './components/GraphPage.jsx'

import Motors from './components/motors/Motors.jsx';

import { OdinSequencer } from 'odin-sequencer-react-ui';

// import plotly from 'plotly.js-dist-min';


function App() {

  // axios.defaults.baseURL = process.env.REACT_APP_ENDPOINT_URL;

  const endpoint_url = import.meta.env.VITE_ENDPOINT_URL;

  const sequencerEndpoint = useAdapterEndpoint('sequencer', endpoint_url, 1000);

  return (
    <OdinApp title="LiveX Controls" navLinks={["Metadata and Setup", "Sequencer", "Furnace Control", "Camera Control", "Monitoring", "Inferencing", "Motors"]}>
      <Row>
        <Col xs={12}>
          <Metadata
            endpoint_url={endpoint_url}
          />
        </Col>
        <Col xs={12}>
          <Trigger
            endpoint_url={endpoint_url}>
          </Trigger>
        </Col>
      </Row>
      <Row>
        <OdinSequencer endpoint={sequencerEndpoint}/>
      </Row>
      <Row>
        <FurnacePage/>
      </Row>
      <Row>
        <Cameras
          endpoint_url={endpoint_url}
        />
      </Row>
      <Row>
        <GraphPage
          endpoint_url={endpoint_url}
        />
      </Row>
      <Row>
        <InferencePage
          endpoint_url={endpoint_url}
        />
      </Row>
      <Row>
        <Motors
          endpoint_url={endpoint_url}
        />
      </Row>
    </OdinApp>
  );
}

export default App;