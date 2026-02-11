import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';
import { useAdapterEndpoint } from 'odin-react';
import MonitorGraph from './furnace/MonitorGraph';


function GraphPage(props) {
    const { endpoint_url } = props;
    const graphEndPoint = useAdapterEndpoint('graph', endpoint_url, 200);

    return (
      <Row>
        <Col xs={12} sm={12} lg={12} xl={6} xxl={6}>
        <MonitorGraph
          endpoint={graphEndPoint}
          paths={[
          'temperature_a/data',
          'temperature_b/data',
          'setpoint_a/data',
          'setpoint_b/data',
          ]}
          seriesNames={['TCA', 'TCB', 'SPA', 'SPB']}
          title={"Temperature and Setpoint Graph"}
        ></MonitorGraph>
        </Col>
        <Col xs={12} sm={12} xl={6} xxl={6}>
        <MonitorGraph
          endpoint={graphEndPoint}
          paths={['output_a/data', 'output_b/data']}
          seriesNames={['POA','POB']}
          title={"PID Output Graph"}
        ></MonitorGraph>
        </Col>
      </Row>
    )
}

export default GraphPage;