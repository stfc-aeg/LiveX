import React from 'react';
import { useState, useEffect } from 'react';
import Col from 'react-bootstrap/Col';
import { Container, Stack } from 'react-bootstrap';
import Form from 'react-bootstrap/Form';
import Row from 'react-bootstrap/Row';
import Button from 'react-bootstrap/Button';
import InputGroup from 'react-bootstrap/InputGroup';
import { OdinGraph, TitleCard, WithEndpoint } from 'odin-react';

const EndPointFormControl = WithEndpoint(Form.Control);
const EndPointButton = WithEndpoint(Button);

function TemperatureGraph(props) {
    const {graphEndPoint} = props;

    // Might need changing or removing
    const connectedPuttingDisable = (!(graphEndPoint.data?.loop_running?.connected || false)) || (graphEndPoint.loading == "putting")

    const [tempData, changeTempData] = useState([{}]);

    const tempDataA = graphEndPoint.data.data?.temp_a;
    const tempDataB = graphEndPoint.data.data?.temp_b;

    // This allows graph to re-render when the data changes
    // This does mean you can't turn off lines, as the graph re-renders
    // This will require toggles and programmatically iterating over what arrays/series name is provided
    useEffect(() => {
      changeTempData([tempDataA, tempDataB]);
    }, [graphEndPoint.data.data?.temp_a, graphEndPoint.data.data?.temp_b])

    return (
        <Container>
          <Col>
            <TitleCard title="temperature graph">
              <Container>
                <Row>
                  <OdinGraph prop_data={tempData} series_names={["TC1", "TC2"]}>
                  </OdinGraph>
                </Row>
                <Row>
                  <Col md="6">
                    <InputGroup>
                    <InputGroup.Text>
                      View previous
                    </InputGroup.Text>
                    {/* <EndPointFormControl endpoint={graphEndPoint} type="number" fullpath="temperature_graph/view_minutes" disabled={connectedPuttingDisable}></EndPointFormControl> */}
                    <InputGroup.Text>
                      minute(s)
                    </InputGroup.Text>
                    </InputGroup>
                  </Col>
                  <Col md="3"></Col>
                  <Col md="3">
                    {/* <EndPointButton endpoint={graphEndPoint} value={true} fullpath="temperature_graph/reset_history" event_type="click" 
                    disabled={connectedPuttingDisable}>
                      Clear Historical Data
                    </EndPointButton> */}
                  </Col>
                </Row>
              </Container>
            </TitleCard>
          </Col>
        </Container>
    )
}

export default TemperatureGraph;