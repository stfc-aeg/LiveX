import React from 'react';
import { useState, useEffect } from 'react';
import Col from 'react-bootstrap/Col';
import { Container } from 'react-bootstrap';
import Form from 'react-bootstrap/Form';
import Row from 'react-bootstrap/Row';
import Button from 'react-bootstrap/Button';
import InputGroup from 'react-bootstrap/InputGroup';
import { OdinGraph, TitleCard, WithEndpoint } from 'odin-react';

const EndPointFormControl = WithEndpoint(Form.Control);
const EndPointButton = WithEndpoint(Button);

function TemperatureGraph(props) {
    const {liveXEndPoint} = props;
    const {connectedPuttingDisable} = props;

    const [tempData, changeTempData] = useState([{}]);

    const tempDataA = liveXEndPoint.data.temp_monitor?.temperature_a;
    const tempDataB = liveXEndPoint.data.temp_monitor?.temperature_b;

    // Graph re-renders when data changes
    useEffect(() => {
      changeTempData([tempDataA, tempDataB]);
    }, [liveXEndPoint.data.temp_monitor?.temperature_a, liveXEndPoint.data.temp_monitor?.temperature_b]
    )

    return (
        <Container>
          <Col>
            <TitleCard title="temperature graph">
              <Container>
                <Row>
                  <OdinGraph 
                  prop_data={tempData}
                  series_names={["TC1", "TC2"]}>
                  </OdinGraph>
                </Row>
              </Container>
            </TitleCard>
          </Col>
        </Container>
    )
}

export default TemperatureGraph;