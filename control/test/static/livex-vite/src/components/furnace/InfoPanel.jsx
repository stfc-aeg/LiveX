import React from 'react';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';
import InputGroup from 'react-bootstrap/InputGroup';
import { TitleCard } from 'odin-react';
import { checkNull, usePrevious } from '../../utils';

function InfoPanel(props) {
    const {furnaceEndPoint} = props;

    const lastInput_a = usePrevious(furnaceEndPoint.data?.pid_a?.temperature);
    const lastInput_b = usePrevious(furnaceEndPoint.data?.pid_b?.temperature);

    // Fixing the label width of the display labels so that they're consistent
    // ~6px per character.
    const labelWidth = 80;
    const valueWidth = 65;

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
        <label>Extra Thermocouples</label>
        <Col xs={4} md={6} xl={4}>
          <InputGroup>
            <InputGroup.Text style={{width:labelWidth}}>
              {furnaceEndPoint.data?.thermocouples?.thermocouple_extra_1?.label ? furnaceEndPoint.data?.thermocouples?.thermocouple_extra_1?.label : 'Not in use'}
            </InputGroup.Text>
            <InputGroup.Text
              style={labelStyling}>
                {checkNull(furnaceEndPoint.data?.thermocouples?.thermocouple_extra_1?.value)}
              </InputGroup.Text>
          </InputGroup>
          <InputGroup>
            <InputGroup.Text style={{width:labelWidth}}>
              {furnaceEndPoint.data?.thermocouples?.thermocouple_extra_2?.label ? furnaceEndPoint.data?.thermocouples?.thermocouple_extra_2?.label : 'Not in use'}
            </InputGroup.Text>
            <InputGroup.Text
              style={labelStyling}>
                {checkNull(furnaceEndPoint.data?.thermocouples?.thermocouple_extra_2?.value)}
                </InputGroup.Text>
          </InputGroup>
        </Col>
        <Col xs={4} md={6} xl={4}>
          <InputGroup>
            <InputGroup.Text style={{width:labelWidth}}>
              {furnaceEndPoint.data?.thermocouples?.thermocouple_extra_3?.label ? furnaceEndPoint.data?.thermocouples?.thermocouple_extra_3?.label : 'Not in use'}
            </InputGroup.Text>
            <InputGroup.Text
              style={labelStyling}>
                {checkNull(furnaceEndPoint.data?.thermocouples?.thermocouple_extra_3?.value)}
                </InputGroup.Text>
          </InputGroup>
          <InputGroup>
            <InputGroup.Text style={{width:labelWidth}}>
              {furnaceEndPoint.data?.thermocouples?.thermocouple_extra_4?.label ? furnaceEndPoint.data?.thermocouples?.thermocouple_extra_4?.label : 'Not in use'}
            </InputGroup.Text>
            <InputGroup.Text
              style={labelStyling}>
                {checkNull(furnaceEndPoint.data?.thermocouples?.thermocouple_extra_4?.value)}
                </InputGroup.Text>
          </InputGroup>
        </Col>
      </Row>
      <Row className="mt-3">
        <Col xs={6} xl={4}>
          <label>PID A</label>
          <Row>
            <InputGroup>
              <InputGroup.Text style={{width:labelWidth}}>
                PID % Out
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
                  PLC Volt.
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
                P Gain
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
                I Sum Diff.
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
                D Sum Diff.
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
                Out Sum
              </InputGroup.Text>
              <InputGroup.Text style={labelStyling}>
              {checkNull(furnaceEndPoint.data.pid_a?.outputsum)}
              </InputGroup.Text>
            </InputGroup>
          </Row>
        </Col>
        <Col xs={6} xl={4}>
          <label>PID B</label>
          <Row>
            <InputGroup>
              <InputGroup.Text style={{width:labelWidth}}>
                PID % Out
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
                  PLC Volt.
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
                P Gain
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
                I Sum Diff.
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
                D Sum Diff.
              </InputGroup.Text>
              <InputGroup.Text style={labelStyling}>
              {checkNull(
                  furnaceEndPoint.data.pid_b?.derivative
                  * (furnaceEndPoint.data.pid_b?.temperature - lastInput_b))}
              </InputGroup.Text>
            </InputGroup>
          </Row>
          <Row>
            <InputGroup>
              <InputGroup.Text style={{width:labelWidth}}>
                Out Sum
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


export default InfoPanel