import React from 'react';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';
import InputGroup from 'react-bootstrap/InputGroup';
import Button from 'react-bootstrap/Button';
import { TitleCard, WithEndpoint } from 'odin-react';
import { checkNull, usePrevious } from '../../utils';

const EndPointButton = WithEndpoint(Button);

function InfoPanel(props) {
    const {furnaceEndPoint} = props;
    const {connectedPuttingDisable} = props;
    const {title} = props;
    const {pid} = props;

    const lastInput_a = usePrevious(furnaceEndPoint.data?.pid_a?.temperature);
    const lastInput_b = usePrevious(furnaceEndPoint.data?.pid_b?.temperature);

    // Fixing the label width of the display labels so that they're consistent
    // ~6px per character.
    const labelWidth = 120;
    const valueWidth = 60;

    const labelStyling = {
        width: valueWidth,
        border: '1px solid lightblue',
        backgroundColor: '#e0f7ff'
      }

  return (
    <TitleCard title={
      <Row>
        <Col xs={3} className="d-flex align-items-center" style={{fontSize:'1.3rem'}}>Monitor Panel</Col>
      </Row>
    }>
      <Row>
        <Col xs={4}>
          <label>PID A</label>
          <Row>
            <InputGroup>
              <InputGroup.Text style={{width:labelWidth}}>
                PID % Output
              </InputGroup.Text>
              <InputGroup.Text
                style={labelStyling}>
                  {checkNull(furnaceEndPoint.data?.pid_a?.output)}
              </InputGroup.Text>
            </InputGroup>
            </Row>
            <Row>
              <InputGroup>
                <InputGroup.Text style={{width:labelWidth}}>
                  PLC Voltage
                </InputGroup.Text>
                <InputGroup.Text
                  style={labelStyling}>
                    {checkNull((furnaceEndPoint.data?.pid_a?.output) * 0.1 * 0.8)}
                </InputGroup.Text>
              </InputGroup>
            </Row>
          <Row className="mt-3">
            <InputGroup>
              <InputGroup.Text style={{width:labelWidth}}>
                Proportional Gain
              </InputGroup.Text>
              <InputGroup.Text style={labelStyling}>
                {checkNull(
                  furnaceEndPoint.data.pid_a?.proportional
                  * (furnaceEndPoint.data.pid_a?.setpoint - furnaceEndPoint.data.pid_a?.temperature))}
              </InputGroup.Text>
            </InputGroup>
          </Row>
          <Row>
            <InputGroup>
              <InputGroup.Text style={{width:labelWidth}}>
                Integral Sum Diff.
              </InputGroup.Text>
              <InputGroup.Text style={labelStyling}>
                {checkNull(
                  furnaceEndPoint.data.pid_a?.integral
                  * (furnaceEndPoint.data.pid_a?.setpoint - furnaceEndPoint.data.pid_a?.temperature))}
              </InputGroup.Text>
            </InputGroup>
          </Row>
          <Row>
            <InputGroup>
              <InputGroup.Text style={{width:labelWidth}}>
                Derivative Sum Diff.
              </InputGroup.Text>
              <InputGroup.Text style={labelStyling}>
              {checkNull(
                  furnaceEndPoint.data.pid_a?.derivative
                  * (furnaceEndPoint.data.pid_a?.temperature - lastInput_a))}
              </InputGroup.Text>
            </InputGroup>
          </Row>
          <Row>
            <InputGroup>
              <InputGroup.Text style={{width:labelWidth}}>
                PID Output Sum
              </InputGroup.Text>
              <InputGroup.Text style={labelStyling}>
              {checkNull(furnaceEndPoint.data.pid_a?.outputsum)}
              </InputGroup.Text>
            </InputGroup>
          </Row>
        </Col>


        <Col xs={4}>
          <label>PID B</label>
          <Row>
            <InputGroup>
              <InputGroup.Text style={{width:labelWidth}}>
                PID % Output
              </InputGroup.Text>
              <InputGroup.Text
                style={labelStyling}>
                  {checkNull(furnaceEndPoint.data?.pid_b?.output)}
              </InputGroup.Text>
            </InputGroup>
            </Row>
            <Row>
              <InputGroup>
                <InputGroup.Text style={{width:labelWidth}}>
                  PLC Voltage
                </InputGroup.Text>
                <InputGroup.Text
                  style={labelStyling}>
                    {checkNull((furnaceEndPoint.data?.pid_b?.output) * 0.1 * 0.8)}
                </InputGroup.Text>
              </InputGroup>
            </Row>
          <Row className="mt-3">
            <InputGroup>
              <InputGroup.Text style={{width:labelWidth}}>
                Proportional Gain
              </InputGroup.Text>
              <InputGroup.Text style={labelStyling}>
                {checkNull(
                  furnaceEndPoint.data.pid_b?.proportional
                  * (furnaceEndPoint.data.pid_b?.setpoint - furnaceEndPoint.data.pid_b?.temperature))}
              </InputGroup.Text>
            </InputGroup>
          </Row>
          <Row>
            <InputGroup>
              <InputGroup.Text style={{width:labelWidth}}>
                Integral Sum Diff.
              </InputGroup.Text>
              <InputGroup.Text style={labelStyling}>
                {checkNull(
                  furnaceEndPoint.data.pid_b?.integral
                  * (furnaceEndPoint.data.pid_b?.setpoint - furnaceEndPoint.data.pid_b?.temperature))}
              </InputGroup.Text>
            </InputGroup>
          </Row>
          <Row>
            <InputGroup>
              <InputGroup.Text style={{width:labelWidth}}>
                Derivative Sum Diff.
              </InputGroup.Text>
              <InputGroup.Text style={labelStyling}>
              {checkNull(
                  furnaceEndPoint.data.pid_b?.derivative
                  * (furnaceEndPoint.data.pid_b?.temperature - lastInput_a))}
              </InputGroup.Text>
            </InputGroup>
          </Row>
          <Row>
            <InputGroup>
              <InputGroup.Text style={{width:labelWidth}}>
                PID Output Sum
              </InputGroup.Text>
              <InputGroup.Text style={labelStyling}>
              {checkNull(furnaceEndPoint.data.pid_b?.outputsum)}
              </InputGroup.Text>
            </InputGroup>
          </Row>
        </Col>

      </Row>
    </TitleCard>
  )
}
export default InfoPanel;